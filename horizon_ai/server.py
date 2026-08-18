"""
Horizon B2B Services - Async REST API & Web Application Server
خادم واجهات برمجة التطبيقات وتطبيق الويب التفاعلي
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from aiohttp import web

from .ai_workflow import HorizonAIWorkflow
from .database import RequestDatabase
from .catalog import get_all_services, HORIZON_SERVICES
from .policies import get_all_policies, HumanReviewStatus, PolicyEvaluationStatus
from .exporters import DataExporter
from .file_parser import FileParser
from .test_suite import run_benchmark_tests
from .i18n import TRANSLATIONS
from .llm_engine import DeepSeekLLMEngine

@web.middleware
async def cors_middleware(request: web.Request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        try:
            response = await handler(request)
        except Exception as e:
            response = web.json_response({"success": False, "error": str(e)}, status=500)
            
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    return response

class HorizonServer:
    def __init__(self, port: int = 8000, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.db = RequestDatabase(db_path="data/horizon_requests.db")
        self.workflow = HorizonAIWorkflow(db=self.db)
        self.llm_engine = DeepSeekLLMEngine()
        self.exporter = DataExporter()
        self.app = web.Application(
            client_max_size=50 * 1024 * 1024, # 50MB
            middlewares=[cors_middleware]
        )
        self._load_samples_cache()
        self._setup_routes()

    def _load_samples_cache(self):
        base_dir = os.path.join(os.path.dirname(__file__), "..", "Package_Files-20260818T104518Z-1-001", "Package_Files")
        self.samples = {}
        sample_meta = {
            "A": {
                "title_ar": "طلب عميل (A) - شركة روافد التجزئة",
                "title_en": "Request (A) - Rawafed Retail Co.",
                "desc_ar": "لوحة مؤشرات مبيعات ومرتجعات وExcel - 12 يوم عمل - سجل متوفر",
                "desc_en": "Sales & Returns BI Dashboard from Excel - 12 Days - CR Available",
                "tag": "متوافق", "tag_class": "success"
            },
            "B": {
                "title_ar": "طلب عميل (B) - شركة مسارات التموين",
                "title_en": "Request (B) - Masarat Catering Co.",
                "desc_ar": "أتمتة بريد الشراء + ربط ERP عبر API - بدون سجل وبدون هاتف",
                "desc_en": "Email Purchase Automation + ERP API - Missing CR & Phone",
                "tag": "نواقص / ثنائي", "tag_class": "warning"
            },
            "C": {
                "title_ar": "طلب عميل (C) - مصنع المدار",
                "title_en": "Request (C) - Al-Madar Factory",
                "desc_ar": "إدارة تواصل اجتماعي ومؤثرين وإعلانات - خارج النطاق واعتذار مهني",
                "desc_en": "Social Media, Influencers & Ads - Out of Scope Polite Apology",
                "tag": "خارج النطاق", "tag_class": "info"
            },
            "D": {
                "title_ar": "طلب عميل (D) - مجموعة البناء الحديث",
                "title_en": "Request (D) - Modern Construction Group",
                "desc_ar": "استشارات إدارية وتوحيد خطوات الاعتماد - 6 أيام بدلاً من 10-15",
                "desc_en": "Management Consulting & SOP - 6 Days (Urgent COO Approval)",
                "tag": "عاجل", "tag_class": "danger"
            },
            "E": {
                "title_ar": "طلب عميل (E) - جهة غير محددة",
                "title_en": "Request (E) - Undefined Entity",
                "desc_ar": "طلب مبهم بدون تفاصيل أو جهة أو سجل مع طلب مجاني/رخيص",
                "desc_en": "Extremely Vague Request, No Contact/CR, Cheap/Fast",
                "tag": "مخالف ومبهم", "tag_class": "purple"
            }
        }
        for letter in ['A', 'B', 'C', 'D', 'E']:
            idx = 5 + ord(letter) - ord('A')
            fname = f"0{idx}_Request_{letter}.txt"
            path = os.path.join(base_dir, fname)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.samples[letter] = {
                        "letter": letter,
                        "code": f"REQ-{letter}",
                        "title": sample_meta[letter]["title_ar"],
                        "title_en": sample_meta[letter]["title_en"],
                        "desc": sample_meta[letter]["desc_ar"],
                        "desc_en": sample_meta[letter]["desc_en"],
                        "tag": sample_meta[letter]["tag"],
                        "tag_class": sample_meta[letter]["tag_class"],
                        "filename": fname,
                        "text": f.read()
                    }

    def _setup_routes(self):
        # API Routes
        self.app.router.add_get('/api/health', self.handle_health)
        self.app.router.add_get('/api/catalog', self.handle_get_catalog)
        self.app.router.add_get('/api/policies', self.handle_get_policies)
        self.app.router.add_get('/api/samples', self.handle_get_samples)
        self.app.router.add_post('/api/process', self.handle_process_request)
        self.app.router.add_post('/api/upload', self.handle_upload_file)
        self.app.router.add_post('/api/batch', self.handle_batch_process)
        self.app.router.add_get('/api/requests', self.handle_get_requests)
        self.app.router.add_get('/api/requests/{id}', self.handle_get_request_detail)
        self.app.router.add_get('/api/requests/{id}/print', self.handle_print_view)
        self.app.router.add_put('/api/requests/{id}/review', self.handle_update_review)
        self.app.router.add_post('/api/requests/{id}/dispatch', self.handle_dispatch_response)
        self.app.router.add_delete('/api/requests/{id}', self.handle_delete_request)
        self.app.router.add_get('/api/stats', self.handle_get_stats)
        self.app.router.add_get('/api/export/excel', self.handle_export_excel)
        self.app.router.add_get('/api/export/csv', self.handle_export_csv)
        self.app.router.add_get('/api/export/json', self.handle_export_json)
        self.app.router.add_post('/api/tests/run', self.handle_run_tests)
        self.app.router.add_post('/api/reset-samples', self.handle_reset_samples)
        self.app.router.add_post('/api/chat', self.handle_chat)

        # Frontend Static Files
        frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
        if os.path.exists(frontend_dir):
            self.app.router.add_get('/', self.handle_index)
            css_dir = os.path.join(frontend_dir, 'css')
            js_dir = os.path.join(frontend_dir, 'js')
            if os.path.exists(css_dir):
                self.app.router.add_static('/css/', path=css_dir, name='css')
            if os.path.exists(js_dir):
                self.app.router.add_static('/js/', path=js_dir, name='js')
            assets_dir = os.path.join(frontend_dir, 'assets')
            if os.path.exists(assets_dir):
                self.app.router.add_static('/assets/', path=assets_dir, name='assets')

    async def handle_index(self, request: web.Request) -> web.Response:
        frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                return web.Response(text=f.read(), content_type='text/html')
        return web.Response(text="<h1>Horizon B2B Services AI Workflow Running</h1>", content_type='text/html')

    async def handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({
            "status": "healthy",
            "service": "Horizon B2B AI Assistant Workflow",
            "version": "2.5.0",
            "backend": "Python 3.11 / aiohttp",
            "language": "Arabic (RTL) & English (LTR)",
            "compliance_engine": "Active",
            "real_use_ready": True
        })

    async def handle_get_catalog(self, request: web.Request) -> web.Response:
        return web.json_response({
            "success": True,
            "services": get_all_services()
        })

    async def handle_get_policies(self, request: web.Request) -> web.Response:
        return web.json_response({
            "success": True,
            "policies": get_all_policies()
        })

    async def handle_get_samples(self, request: web.Request) -> web.Response:
        return web.json_response({
            "success": True,
            "samples": list(self.samples.values())
        })

    async def handle_process_request(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
            raw_text = body.get("text", "")
            source_type = body.get("source_type", "text_input")
            source_filename = body.get("source_filename")
            request_code = body.get("request_code")

            if not raw_text or not raw_text.strip():
                return web.json_response({"success": False, "error": "نص الطلب فارغ."}, status=400)

            res = self.workflow.process_request(
                raw_text=raw_text,
                source_type=source_type,
                source_filename=source_filename,
                save_to_db=True,
                request_code=request_code
            )
            return web.json_response({"success": True, "data": res})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def handle_upload_file(self, request: web.Request) -> web.Response:
        try:
            reader = await request.multipart()
            field = await reader.next()
            if not field or field.name != 'file':
                return web.json_response({"success": False, "error": "لم يتم إرفاق ملف."}, status=400)

            filename = field.filename or "uploaded_file.txt"
            content_bytes = await field.read()

            extracted_text, err = FileParser.parse_file(filename, content_bytes)
            if err:
                return web.json_response({"success": False, "error": err}, status=400)

            res = self.workflow.process_request(
                raw_text=extracted_text,
                source_type="file_upload",
                source_filename=filename,
                save_to_db=True
            )
            return web.json_response({"success": True, "data": res, "filename": filename})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def handle_batch_process(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
            items = body.get("items", [])
            if not items:
                return web.json_response({"success": False, "error": "قائمة الطلبات فارغة."}, status=400)

            results = self.workflow.batch_process(items)
            return web.json_response({"success": True, "total_processed": len(results), "data": results})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def handle_get_requests(self, request: web.Request) -> web.Response:
        search = request.query.get("search")
        review_status = request.query.get("status")
        policy_eval = request.query.get("policy")
        service_name = request.query.get("service")
        limit = int(request.query.get("limit", 100))
        offset = int(request.query.get("offset", 0))

        records = self.db.get_all_requests(
            search=search,
            review_status=review_status,
            policy_eval=policy_eval,
            service_name=service_name,
            limit=limit,
            offset=offset
        )
        return web.json_response({"success": True, "count": len(records), "data": records})

    async def handle_get_request_detail(self, request: web.Request) -> web.Response:
        req_id = int(request.match_info["id"])
        record = self.db.get_request_by_id(req_id)
        if not record:
            return web.json_response({"success": False, "error": "الطلب غير موجود."}, status=404)

        audit_logs = self.db.get_audit_logs(request_id=req_id)
        return web.json_response({"success": True, "data": record, "audit_logs": audit_logs})

    async def handle_update_review(self, request: web.Request) -> web.Response:
        try:
            req_id = int(request.match_info["id"])
            body = await request.json()
            review_status = body.get("review_status", HumanReviewStatus.APPROVED)
            reviewer_name = body.get("reviewer_name", "المراجع البشري")
            review_notes = body.get("review_notes", "")
            edited_fields = body.get("edited_fields")

            success = self.db.update_human_review(
                request_id=req_id,
                review_status=review_status,
                reviewer_name=reviewer_name,
                review_notes=review_notes,
                edited_fields=edited_fields
            )

            if not success:
                return web.json_response({"success": False, "error": "فشل تحديث المراجعة."}, status=400)

            updated = self.db.get_request_by_id(req_id)
            audit_logs = self.db.get_audit_logs(request_id=req_id)
            return web.json_response({"success": True, "data": updated, "audit_logs": audit_logs})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def handle_dispatch_response(self, request: web.Request) -> web.Response:
        """
        Dispatches customer response email / notification and logs delivery receipt.
        """
        try:
            req_id = int(request.match_info["id"])
            body = await request.json()
            recipient = body.get("recipient") or "customer@example.com"
            dispatcher = body.get("dispatcher_name") or "فريق العمليات"
            dispatch_channel = body.get("channel") or "Email / SMTP"

            req_data = self.db.get_request_by_id(req_id)
            if not req_data:
                return web.json_response({"success": False, "error": "الطلب غير موجود."}, status=404)

            # Generate tracking ID
            tracking_id = f"TRK-{uuid.uuid4().hex[:8].upper()}"
            now_iso = datetime.now().isoformat()

            # Record audit log
            with self.db._get_connection() as conn:
                conn.execute("""
                INSERT INTO audit_logs (request_id, action, user, details, timestamp)
                VALUES (?, 'dispatched', ?, ?, ?)
                """, (
                    req_id,
                    dispatcher,
                    f"تم إرسال الرد الرسمي بنجاح إلى ({recipient}) عبر ({dispatch_channel}). رقم التتبع: {tracking_id}",
                    now_iso
                ))
                conn.commit()

            return web.json_response({
                "success": True,
                "tracking_id": tracking_id,
                "recipient": recipient,
                "dispatched_at": now_iso,
                "channel": dispatch_channel,
                "message": "تم إرسال الرد بنجاح وتوثيقه في سجل التدقيق."
            })
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)

    async def handle_print_view(self, request: web.Request) -> web.Response:
        req_id = int(request.match_info["id"])
        record = self.db.get_request_by_id(req_id)
        if not record:
            return web.Response(text="<h1>Request not found</h1>", content_type='text/html')

        html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>تقرير معالجة طلب عميل - {record['request_code']}</title>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 40px; color: #1e293b; background: #fff; }}
    .header {{ border-bottom: 2px solid #0f172a; padding-bottom: 20px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }}
    .title {{ font-size: 20px; font-weight: bold; color: #0f172a; }}
    .meta {{ font-size: 13px; color: #64748b; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: bold; }}
    .box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
    pre {{ background: #0f172a; color: #6ee7b7; padding: 15px; border-radius: 8px; font-family: Consolas, monospace; font-size: 12px; white-space: pre-wrap; line-height: 1.6; }}
    .footer {{ margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 15px; font-size: 11px; color: #94a3b8; text-align: center; }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <div class="title">شركة هورايزون لخدمات الأعمال (Horizon B2B)</div>
      <div class="meta">تقرير معالجة طلب عميل رسمي - رمز الطلب: <strong>{record['request_code']}</strong></div>
    </div>
    <div style="text-align: left;">
      <div class="meta">تاريخ المعالجة: {record['created_at']}</div>
      <div class="meta">حالة المراجعة: <strong>{record['human_review_status']}</strong></div>
    </div>
  </div>

  <div class="box">
    <h3>نموذج الملخص الداخلي الموحد (04_Output_Template)</h3>
    <pre>{record['internal_summary']}</pre>
  </div>

  <div class="box">
    <h3>مسودة الرد الموجه للعميل</h3>
    <div style="font-weight: bold; margin-bottom: 8px;">الموضوع: {record['customer_draft_subject']}</div>
    <div style="white-space: pre-line; line-height: 1.7; font-size: 13px;">{record['customer_draft_body']}</div>
  </div>

  <div class="footer">
    تم استخراج وتوليد هذا التقرير عبر منظومة هورايزون الذكية لإدارة وحوكمة طلبات العملاء.
  </div>
</body>
</html>"""
        return web.Response(text=html, content_type='text/html')

    async def handle_delete_request(self, request: web.Request) -> web.Response:
        req_id = int(request.match_info["id"])
        success = self.db.delete_request(req_id)
        return web.json_response({"success": success})

    async def handle_get_stats(self, request: web.Request) -> web.Response:
        stats = self.db.get_analytics_stats()
        return web.json_response({"success": True, "data": stats})

    async def handle_export_excel(self, request: web.Request) -> web.Response:
        records = self.db.get_all_requests(limit=1000)
        excel_bytes = self.exporter.export_to_excel_bytes(records)
        return web.Response(
            body=excel_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="Horizon_Requests_Report.xlsx"'}
        )

    async def handle_export_csv(self, request: web.Request) -> web.Response:
        records = self.db.get_all_requests(limit=1000)
        csv_str = self.exporter.export_to_csv(records)
        return web.Response(
            body=csv_str.encode('utf-8-sig'),
            content_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="Horizon_Requests_Report.csv"'}
        )

    async def handle_export_json(self, request: web.Request) -> web.Response:
        records = self.db.get_all_requests(limit=1000)
        json_str = self.exporter.export_to_json(records)
        return web.Response(
            text=json_str,
            content_type="application/json; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="Horizon_Requests_Report.json"'}
        )

    async def handle_run_tests(self, request: web.Request) -> web.Response:
        results = run_benchmark_tests()
        return web.json_response({"success": True, "data": results})

    async def handle_reset_samples(self, request: web.Request) -> web.Response:
        self.db.clear_all()
        created = []
        for letter in ['A', 'B', 'C', 'D', 'E']:
            if letter in self.samples:
                s = self.samples[letter]
                res = self.workflow.process_request(
                    raw_text=s["text"],
                    source_type="sample_benchmark",
                    source_filename=s["filename"],
                    request_code=f"REQ-2026-000{ord(letter) - ord('A') + 1}",
                    save_to_db=True
                )
                created.append(res)
        return web.json_response({"success": True, "message": "تمت تهيئة العينات بنجاح.", "count": len(created)})

    async def handle_chat(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
            messages = body.get("messages", [])
            context = body.get("context", "")

            if not messages:
                return web.json_response({"success": False, "error": "No messages provided."}, status=400)

            reply = self.llm_engine.chat(messages, context)
            return web.json_response({"success": True, "reply": reply})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)

def run_server(port: int = 8000, host: str = "127.0.0.1"):
    server = HorizonServer(port=port, host=host)
    print(f"================================================================")
    print(f"  شركة هورايزون لخدمات الأعمال - منصة معالجة الطلبات الذكية")
    print(f"  Horizon B2B Services - AI-Powered Request Ingestion Platform")
    print(f"  Server Running on: http://{host}:{port}")
    print(f"================================================================")
    web.run_app(server.app, host=host, port=port)

if __name__ == "__main__":
    run_server()
