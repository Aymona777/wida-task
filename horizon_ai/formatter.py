"""
Horizon B2B Services - Output Template & Response Formatter
منسق المخرجات الموحدة ونماذج الردود على العملاء
"""

from typing import List, Dict, Any, Optional
from .extractor import ExtractedRequestData
from .matcher import MatchingResult
from .policy_engine import PolicyEvaluationResult
from .policies import HumanReviewStatus

class OutputFormatter:
    """
    Generates standardized internal summaries exactly according to 04_Output_Template.txt
    and drafts professional Arabic customer email/message responses.
    """

    def format_internal_summary(
        self,
        extracted: ExtractedRequestData,
        matched: MatchingResult,
        policy_eval: PolicyEvaluationResult,
        human_review_status: str = HumanReviewStatus.PENDING,
        reviewer_name: Optional[str] = None
    ) -> str:
        """
        Builds the exact standardized internal summary text according to 04_Output_Template.txt.
        """
        # 1. Organization Name
        org_str = extracted.organization_name if extracted.organization_name else "غير مذكور"

        # 2. Contact Person and Title
        if extracted.contact_person != "غير مذكور":
            if extracted.contact_title != "غير مذكورة":
                contact_str = f"{extracted.contact_person} - {extracted.contact_title}"
            else:
                contact_str = extracted.contact_person
        else:
            contact_str = "غير مذكور"

        # 3. Contact Channel
        channel_str = extracted.contact_channel if extracted.contact_channel else "غير مذكور"

        # 4. Requirement Summary
        req_str = extracted.requirement_summary if extracted.requirement_summary else "غير مذكور"

        # 5. Primary Service
        primary_service_str = matched.primary_service_name

        # 6. Secondary Service
        secondary_service_str = matched.secondary_service_name

        # 7. Commercial Registration
        cr_str = policy_eval.cr_evaluation

        # 8. Requested Deadline
        deadline_str = extracted.requested_deadline_text if extracted.requested_deadline_text else "غير محدد"

        # 9. Policy Evaluation
        policy_str = policy_eval.policy_status

        # 10. Missing Data
        if policy_eval.missing_data_list and len(policy_eval.missing_data_list) > 0:
            missing_str = "، ".join(policy_eval.missing_data_list)
        else:
            missing_str = "لا توجد"

        # 11. Important Alerts / Warnings
        if policy_eval.critical_alerts and len(policy_eval.critical_alerts) > 0:
            alerts_str = " | ".join(policy_eval.critical_alerts)
        else:
            alerts_str = "لا توجد قيود استثنائية"

        # 12. Suggested Next Step
        next_step_str = policy_eval.suggested_next_step

        # 13. Human Review Status
        if human_review_status == HumanReviewStatus.APPROVED and reviewer_name:
            review_str = f"تمت المراجعة والاعتماد بواسطة ({reviewer_name})"
        else:
            review_str = human_review_status

        template = (
            "نموذج الملخص الداخلي الموحد\n"
            "============================\n\n"
            "[ملخص معالجة طلب عميل]\n\n"
            f"- اسم الجهة: {org_str}\n"
            f"- شخص التواصل وصفته: {contact_str}\n"
            f"- وسيلة التواصل: {channel_str}\n"
            f"- ملخص الاحتياج: {req_str}\n"
            f"- الخدمة الأساسية المقترحة: {primary_service_str}\n"
            f"- الخدمة الثانوية إن وجدت: {secondary_service_str}\n"
            f"- السجل التجاري: {cr_str}\n"
            f"- الموعد المطلوب: {deadline_str}\n"
            f"- تقييم السياسات: {policy_str}\n"
            f"- البيانات الناقصة: {missing_str}\n"
            f"- التنبيهات المهمة: {alerts_str}\n"
            f"- الخطوة التالية المقترحة: {next_step_str}\n"
            f"- حالة المراجعة البشرية: {review_str}\n"
        )
        return template

    def generate_draft_customer_response(
        self,
        extracted: ExtractedRequestData,
        matched: MatchingResult,
        policy_eval: PolicyEvaluationResult
    ) -> Dict[str, str]:
        """
        Drafts a high-quality, courteous Arabic email / message for the customer
        tailored to the specific status (Acceptance, Urgent Notice, Info Request, Apology).
        """
        greeting_name = extracted.contact_person if extracted.contact_person != "غير مذكور" else "عزيزنا العميل"
        org_name = f" في {extracted.organization_name}" if extracted.organization_name != "غير مذكور" else ""

        # Case 1: Out of Scope (Polite Apology)
        if policy_eval.is_out_of_scope:
            subject = f"بخصوص طلبكم لدى شركة هورايزون لخدمات الأعمال - {extracted.organization_name}"
            body = (
                f"السيد/ة {greeting_name} المحترم/ة،\n"
                f"تحية طيبة وبعد،،\n\n"
                f"نشكركم على ثقتكم وتواصلكم مع شركة هورايزون لخدمات الأعمال{org_name}.\n\n"
                f"نود إحاطتكم بأنه بعد مراجعة تفاصيل طلبكم، فإن هذا النوع من الخدمات ({matched.matched_keywords[0] if matched.matched_keywords else 'الخدمات المطلوبة'}) "
                f"يقع خارج نطاق اختصاصاتنا وخدماتنا المعتمدة، حيث ينصب تركيز هورايزون الأساسي على الاستشارات الإدارية والتحول التشغيلي، وأتمتة العمليات، وتطوير الأنظمة المخصصة وذكاء الأعمال.\n\n"
                f"نعتذر عن تعذر تنفيذ هذا الطلب، ويسعدنا دائماً خدمتكم في أي من مجالاتنا الاستشارية والتقنية مستقبلاً.\n\n"
                f"وتفضلوا بقبول فائق الاحترام والتقدير،،\n"
                f"فريق علاقات العملاء - شركة هورايزون لخدمات الأعمال"
            )
            return {"subject": subject, "body": body, "type": "out_of_scope_apology"}

        # Case 2: Vague / Severe Missing Info
        if policy_eval.has_policy_violations and matched.is_ambiguous:
            subject = f"استكمال متطلبات طلبكم - شركة هورايزون لخدمات الأعمال"
            missing_items = "\n".join([f"  • {item}" for item in policy_eval.missing_data_list])
            body = (
                f"السيد/ة {greeting_name} المحترم/ة،\n"
                f"تحية طيبة وبعد،،\n\n"
                f"نشكركم على اهتمامكم بخدمات شركة هورايزون لخدمات الأعمال.\n\n"
                f"لتمكين فريقنا الاستشاري والتقني من دراسة طلبكم بدقة وتحديد الحل والجدول الزمني الأنسب، نرجو التكرم بتزويدنا بالبيانات التالية:\n"
                f"{missing_items}\n\n"
                f"يسرنا التنسيق معكم لعقد جلسة استكشافية قصيرة لفهم متطلباتكم وتقديم المقترح المناسب.\n\n"
                f"شاكرين ومقدرين حسن تعاونكم،،\n"
                f"فريق تطوير الأعمال - شركة هورايزون لخدمات الأعمال"
            )
            return {"subject": subject, "body": body, "type": "clarification_request"}

        # Case 3: Urgent / Rush Timeline
        if policy_eval.is_urgent:
            subject = f"تأكيد استلام الطلب ومراجعة الموعد العاجل - {extracted.organization_name}"
            body = (
                f"السيد/ة {greeting_name} المحترم/ة،\n"
                f"تحية طيبة وبعد،،\n\n"
                f"نشكركم على تواصلكم مع شركة هورايزون لخدمات الأعمال{org_name}.\n\n"
                f"تم استلام طلبكم المتعلق بـ ({matched.primary_service_name})، ونود التوضيح أن الموعد المستهدف المحدد من قبلكم ({extracted.requested_deadline_text}) "
                f"يصنف كمسار عاجل نظراً لأن الزمن القياسي لإنجاز هذه الخدمة بجودة معتمدة هو ({policy_eval.sla_info}).\n\n"
                f"يجري حالياً عرض الطلب على إدارة العمليات لدراسة إمكانية تسريع التنفيذ وتطبيق خطة العمل المضغوطة ورسوم الاستعجال، وسنوافيكم بالرد النهائي والعرض الفني خلال 24 ساعة.\n\n"
                f"شاكرين لكم تفهمكم،،\n"
                f"إدارة العمليات - شركة هورايزون لخدمات الأعمال"
            )
            return {"subject": subject, "body": body, "type": "urgent_timeline_notice"}

        # Case 4: Compliant Request (with or without missing CR)
        subject = f"تأكيد استلام طلبكم - {matched.primary_service_name} | هورايزون لخدمات الأعمال"
        cr_clause = ""
        if policy_eval.cr_evaluation != "متوفر":
            cr_clause = "\n\nملاحظة: نرجو التكرم بتزويدنا بنسخة من السجل التجاري الساري لاعتماده تمهيداً لبدء التنفيذ الرسمي وفق سياسات الشركة.\n"

        body = (
            f"السيد/ة {greeting_name} المحترم/ة،\n"
            f"تحية طيبة وبعد،،\n\n"
            f"يسعدنا تأكيد استلام طلبكم الخاص بـ ({extracted.exact_requirement[:100]}...).\n\n"
            f"تمت مطابقة احتياجكم مع خدمة ({matched.primary_service_name}) بزمن تنفيذ متوقع ({policy_eval.sla_info})، "
            f"ويعمل فريقنا حالياً على إعداد العرض الفني ونموذج العمل المتوافق مع احتياجاتكم.{cr_clause}\n"
            f"سيتواصل معكم ممثلنا المخصص خلال يوم عمل واحد لتأكيد التفاصيل النهائية.\n\n"
            f"وتفضلوا بقبول خالص الشكر والتقدير،،\n"
            f"فريق خدمة العملاء - شركة هورايزون لخدمات الأعمال"
        )
        return {"subject": subject, "body": body, "type": "standard_acceptance"}
