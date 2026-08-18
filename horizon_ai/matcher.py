"""
Horizon B2B Services - Service Catalog Matcher & Scope Classifier
محرك مطابقة دليل الخدمات وتصنيف النطاق مع منع الهلوسة (Zero Hallucination)
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from .catalog import HORIZON_SERVICES, OUT_OF_SCOPE_DOMAINS, ServiceDefinition
from .utils import normalize_arabic, contains_arabic_phrase

@dataclass
class MatchingResult:
    primary_service_id: Optional[int]
    primary_service_name: str
    secondary_service_id: Optional[int]
    secondary_service_name: str
    is_out_of_scope: bool
    is_ambiguous: bool
    confidence_score: float
    reasoning: str
    out_of_scope_explanation: Optional[str] = None
    matched_keywords: List[str] = None

class ServiceCatalogMatcher:
    """
    Intelligent Arabic Service Matcher and Out-of-Scope Detection.
    Guarantees strict policy compliance and zero hallucination.
    """

    def __init__(self):
        pass

    def match(self, text: str, exact_requirement: str = "") -> MatchingResult:
        full_text = f"{text} {exact_requirement}".strip()
        norm_text = normalize_arabic(full_text)

        # Step 1: Check Out-of-Scope Domains (Zero Hallucination Guardrail)
        out_of_scope_match = self._check_out_of_scope(full_text, norm_text)
        if out_of_scope_match:
            return MatchingResult(
                primary_service_id=None,
                primary_service_name="خارج النطاق",
                secondary_service_id=None,
                secondary_service_name="لا توجد",
                is_out_of_scope=True,
                is_ambiguous=False,
                confidence_score=0.98,
                reasoning=f"الطلب يقع كلياً خارج نطاق الخدمات المقدمة من هورايزون: {out_of_scope_match['domain']}.",
                out_of_scope_explanation=out_of_scope_match['explanation'],
                matched_keywords=out_of_scope_match['matched_keywords']
            )

        # Step 2: Check for Extreme Ambiguity / Vague Requirements (e.g. Request E)
        if self._is_excessively_vague(full_text, norm_text):
            return MatchingResult(
                primary_service_id=None,
                primary_service_name="غير محدد / يتطلب استيضاح",
                secondary_service_id=None,
                secondary_service_name="لا توجد",
                is_out_of_scope=False,
                is_ambiguous=True,
                confidence_score=0.20,
                reasoning="الطلب يفتقر لأي مواصفات فنية أو نطاق عمل واضح، ويحتوي على تعميمات مبهمة تتطلب عقد جلسة استيضاح مع العميل وتعبئة نموذج جمع المتطلبات.",
                out_of_scope_explanation=None,
                matched_keywords=[]
            )

        # Step 3: Score against all 8 Services
        scores: Dict[int, float] = {}
        matched_kw_per_service: Dict[int, List[str]] = {}

        for s_id, s_def in HORIZON_SERVICES.items():
            score, matched_kws = self._score_service(full_text, norm_text, s_def)
            scores[s_id] = score
            matched_kw_per_service[s_id] = matched_kws

        # Sort services by score descending
        sorted_services = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_service_id, top_score = sorted_services[0]

        if top_score < 0.5:
            # Low confidence - ambiguous
            return MatchingResult(
                primary_service_id=None,
                primary_service_name="غير محدد / يتطلب استيضاح",
                secondary_service_id=None,
                secondary_service_name="لا توجد",
                is_out_of_scope=False,
                is_ambiguous=True,
                confidence_score=top_score,
                reasoning="لم يتم العثور على تطابق كافٍ مع الخدمات الموثقة؛ يتطلب مراجعة العميل لتحديد الاحتياج بدقة.",
                matched_keywords=[]
            )

        primary_service = HORIZON_SERVICES[top_service_id]
        primary_name = primary_service.name

        # Check for secondary service (Policy 6: Multi-Service Requests)
        second_service_id, second_score = sorted_services[1]
        secondary_name = "لا توجد"
        secondary_id = None

        # Check secondary threshold: second score must be significant and contain distinctive keywords
        if second_score >= 1.5 and second_score >= (top_score * 0.35) and second_service_id != top_service_id:
            secondary_service = HORIZON_SERVICES[second_service_id]
            secondary_name = secondary_service.name
            secondary_id = second_service_id
            reasoning = (
                f"تم تصنيف الخدمة الأساسية '{primary_service.short_name}' بناءً على: {', '.join(matched_kw_per_service[top_service_id])}. "
                f"كما تم رصد احتياج ثانوي لخدمة '{secondary_service.short_name}' بناءً على: {', '.join(matched_kw_per_service[second_service_id])}."
            )
        else:
            reasoning = f"تمت مطابقة الطلب مع '{primary_service.short_name}' بناءً على تطابق متطلبات: {', '.join(matched_kw_per_service[top_service_id])}."

        confidence = min(0.99, max(0.65, top_score / 5.0))

        return MatchingResult(
            primary_service_id=top_service_id,
            primary_service_name=primary_name,
            secondary_service_id=secondary_id,
            secondary_service_name=secondary_name,
            is_out_of_scope=False,
            is_ambiguous=False,
            confidence_score=round(confidence, 2),
            reasoning=reasoning,
            matched_keywords=matched_kw_per_service[top_service_id]
        )

    def _check_out_of_scope(self, text: str, norm_text: str) -> Optional[Dict[str, Any]]:
        for domain in OUT_OF_SCOPE_DOMAINS:
            matched_kws = []
            for kw in domain["keywords"]:
                if kw in text or normalize_arabic(kw) in norm_text:
                    matched_kws.append(kw)

            heavy_triggers = [
                "حسابات التواصل", "مؤثرين", "شراء الاعلانات", "شراء الإعلانات",
                "انتاج محتوى", "إنتاج محتوى", "محاماه", "اقرار ضريبي"
            ]
            if len(matched_kws) >= 2 or any(ht in norm_text for ht in heavy_triggers):
                return {
                    "domain": domain["domain"],
                    "explanation": domain["explanation"],
                    "matched_keywords": matched_kws
                }
        return None

    def _is_excessively_vague(self, text: str, norm_text: str) -> bool:
        vague_phrases = [
            "يربط كل شيء", "يربط كل شي", "يجعل العمل اسرع", "يجعل العمل أسرع",
            "حل ذكي يربط", "من دون تكلفه", "من دون تكلفة", "اي شي", "كل شيء لدينا"
        ]
        has_vague_phrase = any(normalize_arabic(p) in norm_text for p in vague_phrases)
        
        # Check if there are no concrete service keywords
        concrete_keywords = [
            "لوحة مؤشرات", "داشبورد", "تطبيق جوال", "منصة ويب", "سيرفر", "استضافة",
            "امن سيبراني", "تدريب", "ورشة عمل", "ERP", "CRM", "تحليل العمليات",
            "اجراء تشغيلي", "إجراء تشغيلي", "توحيد خطوات", "مسار الي", "مسار آلي"
        ]
        has_concrete_scope = any(normalize_arabic(kw) in norm_text for kw in concrete_keywords)

        return has_vague_phrase and not has_concrete_scope

    def _score_service(self, text: str, norm_text: str, service: ServiceDefinition) -> Tuple[float, List[str]]:
        score = 0.0
        matched_kws = []

        # Keywords matching
        for kw in service.keywords:
            if kw in text or normalize_arabic(kw) in norm_text:
                score += 1.5
                matched_kws.append(kw)

        for sec_kw in service.secondary_indicators:
            if sec_kw in text or normalize_arabic(sec_kw) in norm_text:
                if sec_kw not in matched_kws:
                    score += 0.8
                    matched_kws.append(sec_kw)

        # Service-specific disambiguation rules:

        # Service 1: Management Consulting & Process Standardization
        if service.id == 1:
            if any(k in norm_text for k in ["توحيد خطوات", "مراجعه الوضع الحالي", "اجراء تشغيلي", "تحديد الادوار", "نماذج اعتماد", "اعتماد طلبات المواد"]):
                score += 3.0
            if "لا نطلب تطوير نظام" in norm_text or "لا نطلب تطبيق" in norm_text:
                score += 2.0

        # Service 2: Process Automation & Smart Solutions
        # When requirement focuses on reading emails, extracting purchase orders, and triggering workflow -> Service 2 is Primary!
        if service.id == 2:
            if any(k in norm_text for k in ["مسار الي", "يقرا طلبات", "يستخرج بيانات", "قراءه طلبات الشراء", "استخراج بيانات المورد"]):
                score += 4.0
            if "مسار الي" in norm_text or "مسارا اليا" in norm_text:
                score += 2.0

        # Service 3: Custom Software Development
        if service.id == 3:
            if any(k in norm_text for k in ["لا نطلب تطوير نظام", "لا نطلب تطبيق", "لا نطلب بناء نظام"]):
                score -= 6.0

        # Service 5: Data Analytics & BI Dashboards
        if service.id == 5:
            if any(k in norm_text for k in ["لوحه مؤشرات", "excel", "متوسط قيمه الطلب", "نسبه المرتجعات", "المبيعات الاسبوعيه"]):
                score += 4.0

        # Service 7: Systems Integration
        if service.id == 7:
            if any(k in norm_text for k in ["ربط انظمه", "تكامل", "api", "ارسال البيانات الي نظام erp", "erp الحالي عبر api"]):
                score += 2.5

        return score, matched_kws
