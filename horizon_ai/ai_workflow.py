"""
Horizon B2B Services - Master AI Workflow Pipeline
خط سير العمل الذكي المتكامل لمعالجة طلبات العملاء (AI Workflow Pipeline)
"""

import time
from typing import Dict, Any, Optional, List
from .extractor import RequestExtractor, ExtractedRequestData
from .matcher import ServiceCatalogMatcher, MatchingResult
from .policy_engine import PolicyEngine, PolicyEvaluationResult
from .formatter import OutputFormatter
from .database import RequestDatabase
from .policies import HumanReviewStatus

class HorizonAIWorkflow:
    """
    End-to-End Autonomous AI Workflow for processing Horizon B2B Customer Requests.
    Fulfills all 8 core system requirements:
    1. Request Reception & Processing
    2. Data Extraction
    3. Classification & Service Directory Matching
    4. Policy Enforcement & Urgency/Violation Detection
    5. Output Formatting (Standard Internal Summary Template)
    6. Automated Data Store (SQLite / Excel / CSV)
    7. No Hallucination Guardrails
    8. Human-in-the-Loop Review & Approval Integration
    """

    def __init__(self, db: Optional[RequestDatabase] = None):
        self.extractor = RequestExtractor()
        self.matcher = ServiceCatalogMatcher()
        self.policy_engine = PolicyEngine()
        self.formatter = OutputFormatter()
        self.db = db or RequestDatabase()

    def process_request(
        self,
        raw_text: str,
        source_type: str = "text_input",
        source_filename: Optional[str] = None,
        save_to_db: bool = True,
        request_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the complete multi-stage AI workflow pipeline.
        """
        start_time = time.time()
        workflow_steps: List[Dict[str, Any]] = []

        # Stage 1: Reception & Normalization
        stage1_start = time.time()
        cleaned_text = raw_text.strip()
        workflow_steps.append({
            "step": 1,
            "title": "استلام الطلب وتطبيع النص",
            "status": "success",
            "duration_ms": round((time.time() - stage1_start) * 1000, 2),
            "details": f"تم استلام النص بطول {len(cleaned_text)} حرفاً بنجاح."
        })

        # Stage 2: Entity & Data Extraction
        stage2_start = time.time()
        extracted: ExtractedRequestData = self.extractor.extract(cleaned_text)
        workflow_steps.append({
            "step": 2,
            "title": "استخراج الكيانات والبيانات الأساسية",
            "status": "success",
            "duration_ms": round((time.time() - stage2_start) * 1000, 2),
            "details": f"الجهة: {extracted.organization_name} | شخص التواصل: {extracted.contact_person} | السجل: {extracted.cr_status}"
        })

        # Stage 3: Service Catalog Matching & Scope Verification (Zero Hallucination)
        stage3_start = time.time()
        matched: MatchingResult = self.matcher.match(cleaned_text, extracted.exact_requirement)
        workflow_steps.append({
            "step": 3,
            "title": "مطابقة دليل الخدمات وفحص النطاق",
            "status": "success" if not matched.is_out_of_scope else "warning",
            "duration_ms": round((time.time() - stage3_start) * 1000, 2),
            "details": f"الخدمة الأساسية: {matched.primary_service_name} | الخدمة الثانوية: {matched.secondary_service_name} (دقة {int(matched.confidence_score * 100)}%)"
        })

        # Stage 4: Policy Enforcement & Compliance Check
        stage4_start = time.time()
        policy_eval: PolicyEvaluationResult = self.policy_engine.evaluate(extracted, matched)
        policy_step_status = "success"
        if policy_eval.has_policy_violations:
            policy_step_status = "danger"
        elif policy_eval.is_urgent:
            policy_step_status = "warning"
        elif policy_eval.is_out_of_scope:
            policy_step_status = "info"

        workflow_steps.append({
            "step": 4,
            "title": "تقييم السياسات وفحص القيود الزمنية والتجارية",
            "status": policy_step_status,
            "duration_ms": round((time.time() - stage4_start) * 1000, 2),
            "details": f"تقييم السياسة: {policy_eval.policy_status} | تنبيهات: {len(policy_eval.critical_alerts)} | نواقص: {len(policy_eval.missing_data_list)}"
        })

        # Stage 5: Output Template & Draft Response Generation
        stage5_start = time.time()
        internal_summary = self.formatter.format_internal_summary(
            extracted=extracted,
            matched=matched,
            policy_eval=policy_eval,
            human_review_status=HumanReviewStatus.PENDING
        )
        draft_response = self.formatter.generate_draft_customer_response(
            extracted=extracted,
            matched=matched,
            policy_eval=policy_eval
        )
        workflow_steps.append({
            "step": 5,
            "title": "توليد الملخص الموحد ومسودة الرد على العميل",
            "status": "success",
            "duration_ms": round((time.time() - stage5_start) * 1000, 2),
            "details": "تم بناء النموذج الداخلي وصياغة مسودة الرد للعميل وفق الهوية المعتمدة."
        })

        total_duration_ms = round((time.time() - start_time) * 1000, 2)

        # Build master record
        record: Dict[str, Any] = {
            "request_code": request_code or self.db.generate_next_code(),
            "source_type": source_type,
            "source_filename": source_filename,
            "raw_text": cleaned_text,
            "organization_name": extracted.organization_name,
            "contact_person": extracted.contact_person,
            "contact_title": extracted.contact_title,
            "contact_channel": extracted.contact_channel,
            "email": extracted.email,
            "phone": extracted.phone,
            "cr_number": extracted.cr_number,
            "cr_status": policy_eval.cr_evaluation,
            "exact_requirement": extracted.exact_requirement,
            "requirement_summary": extracted.requirement_summary,
            "requested_deadline_text": extracted.requested_deadline_text,
            "requested_deadline_days": extracted.requested_deadline_days,
            "primary_service_id": matched.primary_service_id,
            "primary_service_name": matched.primary_service_name,
            "secondary_service_id": matched.secondary_service_id,
            "secondary_service_name": matched.secondary_service_name,
            "policy_evaluation": policy_eval.policy_status,
            "is_urgent": policy_eval.is_urgent,
            "is_out_of_scope": policy_eval.is_out_of_scope,
            "missing_data": policy_eval.missing_data_list,
            "critical_alerts": policy_eval.critical_alerts,
            "suggested_next_step": policy_eval.suggested_next_step,
            "internal_summary": internal_summary,
            "customer_draft_subject": draft_response["subject"],
            "customer_draft_body": draft_response["body"],
            "customer_draft_type": draft_response["type"],
            "human_review_status": HumanReviewStatus.PENDING,
            "confidence_score": matched.confidence_score,
            "sla_info": policy_eval.sla_info,
            "workflow_steps": workflow_steps,
            "total_duration_ms": total_duration_ms
        }

        # Stage 6: Persistent Data Store
        if save_to_db:
            req_id = self.db.save_request(record)
            record["id"] = req_id

        return record

    def batch_process(self, requests_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch processes a list of customer requests.
        """
        results = []
        for item in requests_list:
            text = item.get("text") or item.get("raw_text") or ""
            source_type = item.get("source_type", "batch")
            source_filename = item.get("source_filename")
            req_code = item.get("request_code")
            res = self.process_request(
                raw_text=text,
                source_type=source_type,
                source_filename=source_filename,
                save_to_db=True,
                request_code=req_code
            )
            results.append(res)
        return results
