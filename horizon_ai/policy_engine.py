"""
Horizon B2B Services - Policy Compliance & Governance Engine
محرك تقييم السياسات التشغيلية وضوابط الامتثال
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from .catalog import HORIZON_SERVICES, get_service_by_id
from .policies import PolicyEvaluationStatus, CommercialRegistrationStatus, HORIZON_POLICIES
from .extractor import ExtractedRequestData
from .matcher import MatchingResult

@dataclass
class PolicyEvaluationResult:
    policy_status: str                       # متوافق / عاجل ويتطلب موافقة / مخالف / خارج النطاق
    is_urgent: bool                          # True if requires COO rush approval
    is_compliant: bool                       # True if strictly compliant
    is_out_of_scope: bool                    # True if outside service catalog
    has_policy_violations: bool              # True if breaks < 3 days or critical rules
    cr_evaluation: str                       # متوفر / غير متوفر / غير واضح
    missing_data_list: List[str]             # List of missing essential items
    critical_alerts: List[str]               # Important alerts / warnings
    suggested_next_step: str                 # Concrete recommended action for Sales/Ops
    sla_info: Optional[str] = None           # Expected SLA text
    coo_approval_required: bool = False      # True if COO sign-off is needed

class PolicyEngine:
    """
    Evaluates customer requests against the 8 company operating policies.
    """

    def evaluate(self, extracted: ExtractedRequestData, matched: MatchingResult) -> PolicyEvaluationResult:
        alerts: List[str] = []
        missing_data: List[str] = list(extracted.missing_fields)
        policy_status = PolicyEvaluationStatus.COMPLIANT
        is_urgent = False
        is_compliant = True
        has_violations = False
        coo_approval = False
        sla_info = None

        # 1. Evaluate Commercial Registration (Policy 1)
        cr_eval = extracted.cr_status
        if cr_eval != CommercialRegistrationStatus.AVAILABLE:
            alerts.append("عدم توفر السجل التجاري الساري يمنع التحويل للتنفيذ الرسمي (سياسة 1).")

        # 2. Evaluate Out-of-Scope (Policy 5)
        if matched.is_out_of_scope:
            policy_status = PolicyEvaluationStatus.OUT_OF_SCOPE
            is_compliant = False
            alerts.append(matched.out_of_scope_explanation or "الطلب يقع خارج دليل خدمات الشركة المعتمد (سياسة 5).")
            next_step = (
                "الاعتذار بلباقة للعميل عن تقديم الخدمات التسويقية/غير المدرجة، "
                "وتوضيح نطاق تخصص الشركة في الحلول الاستشارية والتقنية والتحول التشغيلي."
            )
            return PolicyEvaluationResult(
                policy_status=policy_status,
                is_urgent=False,
                is_compliant=False,
                is_out_of_scope=True,
                has_policy_violations=False,
                cr_evaluation=cr_eval,
                missing_data_list=missing_data,
                critical_alerts=alerts,
                suggested_next_step=next_step,
                sla_info="غير منطبق (خارج النطاق)",
                coo_approval_required=False
            )

        # 3. Evaluate Ambiguous / Incomplete Requests (e.g. Request E)
        if matched.is_ambiguous or (len(missing_data) >= 4 and not matched.primary_service_id):
            policy_status = PolicyEvaluationStatus.NON_COMPLIANT
            is_compliant = False
            has_violations = True
            alerts.append("الطلب يفتقر لأدنى متطلبات الوضوح والبيانات الأساسية ونطاق العمل محدد بصورة مبهمة.")
            if extracted.requested_discount_or_free:
                alerts.append("الطلب يتضمن إشارة لخفض التكلفة/المجانية بدون نطاق عمل محدد، وتخضع الأسعار للاعتماد التجاري حصراً (سياسة 7).")
            next_step = "إحالة لمسؤول المبيعات لإرسال نموذج جمع المتطلبات واستيفاء البيانات الأساسية وعقد جلسة استكشافية."
            return PolicyEvaluationResult(
                policy_status="مخالف وغير مكتمل",
                is_urgent=False,
                is_compliant=False,
                is_out_of_scope=False,
                has_policy_violations=True,
                cr_evaluation=cr_eval,
                missing_data_list=missing_data,
                critical_alerts=alerts,
                suggested_next_step=next_step,
                sla_info="يتطلب استيضاح وتحديد النطاق",
                coo_approval_required=False
            )

        # 4. Evaluate Timeline & Minimum Execution Duration (Policies 2 & 3)
        service_def = get_service_by_id(matched.primary_service_id) if matched.primary_service_id else None
        if service_def:
            sla_info = service_def.standard_days_text

        deadline_days = extracted.requested_deadline_days

        if deadline_days is not None:
            # Policy 2: Absolute minimum 3 business days
            if deadline_days < 3:
                policy_status = PolicyEvaluationStatus.NON_COMPLIANT
                is_compliant = False
                has_violations = True
                alerts.append(
                    f"مخالفة لسياسة الحد الأدنى لزمن التنفيذ (سياسة 2): الموعد المطلوب ({deadline_days} أيام) أقل من 3 أيام عمل."
                )
                next_step = f"إشعار العميل بتعذر التسليم خلال {deadline_days} أيام لمخالفته السياسة، واقتراح موعد متوافق (الحد الأدنى {service_def.min_days if service_def else 3} أيام عمل)."

            # Policy 3: Urgent Deadlines (>= 3 days but < standard minimum days of the service)
            elif service_def and deadline_days < service_def.min_days:
                policy_status = PolicyEvaluationStatus.URGENT_NEEDS_APPROVAL
                is_urgent = True
                is_compliant = False
                coo_approval = True
                alerts.append(
                    f"طلب عاجل (سياسة 3): الموعد المطلوب ({deadline_days} أيام عمل) أقل من الزمن القياسي للخدمة ({service_def.standard_days_text}). يتطلب موافقة مدير العمليات وتسعير استعجال."
                )
                next_step = (
                    "العرض على مدير العمليات للموافقة على الجدول المضغوط وتحديد تكلفة الاستعجال "
                    "ثم إعداد مقترح خطة العمل السريعة."
                )
            else:
                # Compliant deadline
                if policy_status == PolicyEvaluationStatus.COMPLIANT:
                    policy_status = PolicyEvaluationStatus.COMPLIANT

        # 5. Check Pricing / Discount / Free work policy (Policy 7)
        if extracted.requested_discount_or_free:
            alerts.append("العميل أشار إلى طلب تكلفة منخفضة أو خصم؛ يمنع تقديم وعود مالية آلياً ويحال الطلب للمبيعات للاعتماد التجاري (سياسة 7).")

        # 6. Multi-service coordination alerts (Policy 6)
        if matched.secondary_service_id:
            alerts.append(f"الطلب يتضمن متطلبات متعددة تجمع بين '{matched.primary_service_name}' و '{matched.secondary_service_name}'.")

        # 7. Formulate Suggested Next Step if not already set
        already_handled_status = policy_status in [PolicyEvaluationStatus.OUT_OF_SCOPE, PolicyEvaluationStatus.URGENT_NEEDS_APPROVAL, PolicyEvaluationStatus.NON_COMPLIANT]
        if not already_handled_status:
            if len(missing_data) > 0:
                missing_str = " و".join(missing_data[:2])
                next_step = f"التواصل مع العميل لاستكمال {missing_str} والبيانات الناقصة، وإحالة المتطلبات الفنية للفريق المختص."
            else:
                next_step = f"إحالة الطلب لفريق {service_def.short_name if service_def else 'المختص'} لإعداد العرض الفني ونطاق العمل والبدء في الإجراءات."

        # If missing critical info like CR or channels, add actionable clause
        if cr_eval != CommercialRegistrationStatus.AVAILABLE and policy_status == PolicyEvaluationStatus.COMPLIANT:
            if "التواصل مع العميل" not in next_step:
                next_step = "طلب السجل التجاري الساري من العميل وتجهيز العرض الفني المبدئي تمهيداً للاعتماد."

        return PolicyEvaluationResult(
            policy_status=policy_status,
            is_urgent=is_urgent,
            is_compliant=is_compliant,
            is_out_of_scope=matched.is_out_of_scope,
            has_policy_violations=has_violations,
            cr_evaluation=cr_eval,
            missing_data_list=missing_data,
            critical_alerts=alerts,
            suggested_next_step=next_step,
            sla_info=sla_info or "حسب طبيعة الطلب",
            coo_approval_required=coo_approval
        )
