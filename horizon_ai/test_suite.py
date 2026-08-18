"""
Horizon B2B Services - Comprehensive Automated Benchmark & Unit Test Suite
جناح الاختبارات الشامل للتحقق من جميع الحالات والحالات الحدية ودقة الامتثال للسياسات
"""

import os
import unittest
from typing import Dict, Any
from .ai_workflow import HorizonAIWorkflow
from .database import RequestDatabase
from .policies import PolicyEvaluationStatus, CommercialRegistrationStatus, HumanReviewStatus
from .catalog import get_all_services
from .policies import get_all_policies
from .exporters import DataExporter
from .file_parser import FileParser

class TestHorizonAIWorkflowComprehensive(unittest.TestCase):
    """
    Complete unit and end-to-end test suite for Horizon AI Workflow.
    """

    @classmethod
    def setUpClass(cls):
        cls.test_db = RequestDatabase(db_path="data/test_horizon_comprehensive.db")
        cls.test_db.clear_all()
        cls.workflow = HorizonAIWorkflow(db=cls.test_db)
        cls.exporter = DataExporter()
        
        # Load package requests
        base_dir = os.path.join(os.path.dirname(__file__), "..", "Package_Files-20260818T104518Z-1-001", "Package_Files")
        cls.requests_texts = {}
        for letter in ['A', 'B', 'C', 'D', 'E']:
            path = os.path.join(base_dir, f"0{5 + ord(letter) - ord('A')}_Request_{letter}.txt")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    cls.requests_texts[letter] = f.read()

    def test_01_request_a_analytics(self):
        """Request A: Data Analytics & BI Dashboard -> 100% Compliant"""
        text = self.requests_texts['A']
        res = self.workflow.process_request(text, source_type="benchmark", request_code="BENCH-A", save_to_db=True)
        
        self.assertIn("روافد التجزئة", res["organization_name"])
        self.assertIn("نورة السالم", res["contact_person"])
        self.assertEqual(res["primary_service_id"], 5)
        self.assertEqual(res["cr_status"], CommercialRegistrationStatus.AVAILABLE)
        self.assertEqual(res["policy_evaluation"], PolicyEvaluationStatus.COMPLIANT)
        self.assertFalse(res["is_urgent"])
        self.assertFalse(res["is_out_of_scope"])
        self.assertEqual(res["secondary_service_name"], "لا توجد")
        self.assertIn("نموذج الملخص الداخلي الموحد", res["internal_summary"])

    def test_02_request_b_automation_and_integration(self):
        """Request B: Automation (Primary) + ERP Integration (Secondary) + Missing CR/Phone"""
        text = self.requests_texts['B']
        res = self.workflow.process_request(text, source_type="benchmark", request_code="BENCH-B", save_to_db=True)
        
        self.assertIn("مسارات التموين", res["organization_name"])
        self.assertIn("ليان", res["contact_person"])
        self.assertEqual(res["primary_service_id"], 2)
        self.assertEqual(res["secondary_service_id"], 7)
        self.assertEqual(res["cr_status"], CommercialRegistrationStatus.NOT_AVAILABLE)
        missing_str = " ".join(res["missing_data"])
        self.assertTrue("السجل التجاري" in missing_str or "سجل" in missing_str)
        self.assertTrue("وسيلة التواصل" in missing_str or "هاتف" in missing_str or "بريد" in missing_str)

    def test_03_request_c_out_of_scope(self):
        """Request C: Social media & influencers -> Strictly Out of Scope (Zero Hallucination)"""
        text = self.requests_texts['C']
        res = self.workflow.process_request(text, source_type="benchmark", request_code="BENCH-C", save_to_db=True)
        
        self.assertIn("مصنع المدار", res["organization_name"])
        self.assertEqual(res["primary_service_name"], "خارج النطاق")
        self.assertTrue(res["is_out_of_scope"])
        self.assertEqual(res["policy_evaluation"], PolicyEvaluationStatus.OUT_OF_SCOPE)
        self.assertIn("الاعتذار", res["suggested_next_step"])
        self.assertEqual(res["customer_draft_type"], "out_of_scope_apology")

    def test_04_request_d_urgent_consulting(self):
        """Request D: Process Standardization & Consulting, 6 days (standard 10-15) -> Urgent"""
        text = self.requests_texts['D']
        res = self.workflow.process_request(text, source_type="benchmark", request_code="BENCH-D", save_to_db=True)
        
        self.assertIn("البناء الحديث", res["organization_name"])
        self.assertIn("فهد العمر", res["contact_person"])
        self.assertEqual(res["primary_service_id"], 1)
        self.assertEqual(res["policy_evaluation"], PolicyEvaluationStatus.URGENT_NEEDS_APPROVAL)
        self.assertTrue(res["is_urgent"])
        self.assertIn("مدير العمليات", res["suggested_next_step"])

    def test_05_request_e_vague_incomplete(self):
        """Request E: Extremely vague, no info, cheap -> Non-compliant / Ambiguous"""
        text = self.requests_texts['E']
        res = self.workflow.process_request(text, source_type="benchmark", request_code="BENCH-E", save_to_db=True)
        
        self.assertIn("غير محدد", res["primary_service_name"])
        self.assertIn("مخالف", res["policy_evaluation"])
        self.assertGreaterEqual(len(res["missing_data"]), 3)
        self.assertIn("نموذج جمع المتطلبات", res["suggested_next_step"])

    def test_06_edge_case_policy_2_violation_less_than_3_days(self):
        """Policy 2: Absolute minimum 3 days. If customer asks for 2 days -> Violation (مخالف)"""
        text = """
        الجهة: شركة النجم السريع
        شخص التواصل: سامي العلي
        وسيلة التواصل: 0555555555
        الاحتياج: بناء لوحة مؤشرات عاجلة جداً
        الموعد المطلوب: خلال يومين فقط.
        السجل التجاري: سجل رقم 1010101010
        """
        res = self.workflow.process_request(text, source_type="test", request_code="EDGE-2DAYS", save_to_db=False)
        self.assertEqual(res["policy_evaluation"], PolicyEvaluationStatus.NON_COMPLIANT)
        self.assertTrue(any("الحد الأدنى لزمن التنفيذ" in alert for alert in res["critical_alerts"]))

    def test_07_edge_case_cloud_and_cybersecurity(self):
        """Service 4: Cloud Infrastructure & Cybersecurity"""
        text = """
        الجهة: شركة التقنية المتقدمة
        شخص التواصل: م. خالد المنصور
        وسيلة التواصل: khaled@example.com
        الاحتياج: تهيئة بيئة سحابية على AWS وإعداد النسخ الاحتياطي وتأمين جدار الحماية ضد الاختراقات
        الموعد المطلوب: خلال 7 أيام عمل
        السجل التجاري: 7000000001
        """
        res = self.workflow.process_request(text, source_type="test", request_code="EDGE-CLOUD", save_to_db=False)
        self.assertEqual(res["primary_service_id"], 4)
        self.assertEqual(res["policy_evaluation"], PolicyEvaluationStatus.COMPLIANT)

    def test_08_edge_case_training_and_capability_building(self):
        """Service 6: Training & Capability Building"""
        text = """
        الجهة: بنك الابتكار
        شخص التواصل: سارة أحمد - مديرة التدريب
        وسيلة التواصل: sara@bank.test
        الاحتياج: عقد ورش عمل وبرنامج تدريبي للموظفين على استخدام أدوات الذكاء الاصطناعي وتوليد المحتوى
        الموعد المطلوب: خلال 5 أيام عمل
        السجل التجاري: 1010202030
        """
        res = self.workflow.process_request(text, source_type="test", request_code="EDGE-TRAIN", save_to_db=False)
        self.assertEqual(res["primary_service_id"], 6)
        self.assertEqual(res["policy_evaluation"], PolicyEvaluationStatus.COMPLIANT)

    def test_09_human_in_the_loop_review_lifecycle(self):
        """HITL Review Lifecycle: Update status, assign reviewer, modify notes, verify audit trail"""
        saved = self.test_db.get_request_by_code("BENCH-A")
        self.assertIsNotNone(saved)
        req_id = saved["id"]

        # Human reviews and approves
        success = self.test_db.update_human_review(
            request_id=req_id,
            review_status=HumanReviewStatus.APPROVED,
            reviewer_name="أحمد المدير التنفيذي",
            review_notes="تمت مراجعة نطاق العمل ومطابقة المتطلبات والاعتماد جاهز للإرسال."
        )
        self.assertTrue(success)

        updated = self.test_db.get_request_by_id(req_id)
        self.assertEqual(updated["human_review_status"], HumanReviewStatus.APPROVED)
        self.assertEqual(updated["reviewer_name"], "أحمد المدير التنفيذي")

        # Check audit log
        logs = self.test_db.get_audit_logs(request_id=req_id)
        self.assertGreaterEqual(len(logs), 2)

    def test_10_data_export_formats(self):
        """Verify CSV and Excel exports contain valid data and UTF-8 encoding"""
        all_reqs = self.test_db.get_all_requests()
        self.assertGreater(len(all_reqs), 0)

        # CSV Export
        csv_str = self.exporter.export_to_csv(all_reqs)
        self.assertTrue(csv_str.startswith('\ufeff'))
        self.assertIn("روافد التجزئة", csv_str)

        # Excel Export
        excel_bytes = self.exporter.export_to_excel_bytes(all_reqs)
        self.assertGreater(len(excel_bytes), 100)

        # JSON Export
        json_str = self.exporter.export_to_json(all_reqs)
        self.assertIn("Horizon B2B Services", json_str)

    def test_11_file_parser(self):
        """Verify FileParser handles text and json correctly"""
        txt_bytes = "الجهة: شركة تجريبية\nالاحتياج: اختبار التحليل".encode('utf-8')
        extracted_text, err = FileParser.parse_file("test.txt", txt_bytes)
        self.assertIsNone(err)
        self.assertIn("شركة تجريبية", extracted_text)

        json_bytes = '{"الجهة": "مؤسسة ذكية", "الاحتياج": "تطوير لوحة مؤشرات"}'.encode('utf-8')
        json_extracted, err2 = FileParser.parse_file("test.json", json_bytes)
        self.assertIsNone(err2)
        self.assertIn("مؤسسة ذكية", json_extracted)

def run_benchmark_tests() -> Dict[str, Any]:
    """
    Runs the benchmark suite and returns formatted results for UI and API.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHorizonAIWorkflowComprehensive)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return {
        "total_tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "was_successful": result.wasSuccessful(),
        "passed": result.testsRun - len(result.failures) - len(result.errors)
    }

if __name__ == "__main__":
    unittest.main()
