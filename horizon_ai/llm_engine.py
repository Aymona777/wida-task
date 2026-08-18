import os
import json
import re
import requests
from typing import Dict, List, Any, Optional, Tuple
from .catalog import get_all_services, get_service_by_id
from .policies import get_all_policies

# Load environment variables from .env if present
def _load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_env_file()

DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://inference.dahl.global/v1/chat/completions")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", os.getenv("HORIZON_AI_API_KEY", ""))
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-ai/DeepSeek-V4-Flash-0731")

SYSTEM_PROMPT_ANALYZE = """أنت المساعد الذكي وخبير العمليات والسياسات لشركة هورايزون لخدمات الأعمال (Horizon B2B Services).
مهمتك هي تحليل طلب العميل الوارد بدقة استنتاجية صارمة، واستخراج كافة البيانات، ومطابقتها مع دليل الخدمات الثمانية وسياسات التشغيل الثمانية المعتمدة، ثم إصدار المخرج المنظم.

### دليل الخدمات المعتمدة (8 خدمات فقط):
1. الاستشارات الإدارية والتحول التشغيلي (10 إلى 15 يوم عمل) - توثيق إجراءات، مؤشرات أداء، هيكلة فرق. (لا تشمل تطوير أنظمة أو حملات تسويقية).
2. أتمتة العمليات والحلول الذكية (5 إلى 10 أيام عمل) - تدفقات آلية، ربط نماذج، استخراج بيانات مستندات. (لا تشمل بناء أنظمة ERP متكاملة).
3. تطوير التطبيقات والحلول الرقمية (15 إلى 30 يوم عمل) - تطبيقات ويب وجوال مخصصة، بوابات عملاء. (لا تشمل صيانة عتاد أو أجهزة).
4. البنية التحتية السحابية والأمن السيبراني (7 إلى 14 يوم عمل) - إعداد سحابي، نسخ احتياطي، مراجعة أمنية. (لا تشمل استضافة مواقع عامة صغيرة).
5. تحليل البيانات ولوحات ذكاء الأعمال (5 إلى 12 يوم عمل) - لوحات Power BI / Tableau / Excel تفاعلية، توحيد مصادر. (لا تشمل إدخال يدوي مستمر).
6. التدريب وبناء القدرات المؤسسية (3 إلى 7 أيام عمل) - ورش تدريبية، أدلة عمل، نقل معرفة. (لا تشمل دورات أكاديمية طويلة).
7. التكامل والربط بين الأنظمة (7 إلى 15 يوم عمل) - ربط API و Webhooks بين الأنظمة وقواعد البيانات. (لا تشمل إعادة كتابة الشيفرة للأنظمة المغلقة).
8. الدعم الفني وإدارة الأنظمة (اشتراك شهري / ربع سنوي) - صيانة دورية، دعم مستخدمين، مراقبة أداء. (لا تشمل تطوير ميزات جديدة).

### سياسات التشغيل وضوابط الامتثال الثمانية:
- سياسة 1: السجل التجاري شرط إلزامي للبدء في التنفيذ الرسمي. إذا لم يرفق نطلب إرفاقه.
- سياسة 2: الحد الأدنى لأي خدمة هو 3 أيام عمل ولا يُقبل أي طلب يطلب مدة أقل من 3 أيام نهائياً.
- سياسة 3: إذا كان الموعد المطلوب أقل من الحد القياسي للخدمة يُصنف "عاجل ويتطلب موافقة" مدير العمليات وتسعير استعجال.
- سياسة 4: يجب أن يحتوي الطلب على اسم الجهة، اسم وصفة المسؤول، ووسيلة اتصال سارية. أي نقص يُسجل في النواقص.
- سياسة 5: الخدمات الخارجة عن النطاق (مثل التسويق الرقمي، إدارة حسابات التواصل الاجتماعي، شراء الإعلانات، تصوير، مشاهير) يُعتذر عنها بلباقة ولا تُقبل نهائياً مع تقديم ملخص وطلب توضيح (Zero Hallucination).
- سياسة 6: إذا تضمن الطلب أكثر من خدمة، تُحدد خدمة أساسية وخدمة ثانوية.
- سياسة 7: تخضع الأسعار للاعتماد التجاري حصراً، ويُمنع تقديم وعود مجانية أو تخفيضات دون نطاق معتمد.
- سياسة 8: تخضع كافة المخرجات للمراجعة البشرية المعتمدة قبل الإرسال.

يجب أن ترجع النتيجة بصيغة JSON حصراً بدون أي كود إضافي بالبنية التالية:
{
  "organization_name": "اسم الجهة أو غير مذكور",
  "contact_person": "اسم المسؤول أو غير مذكور",
  "contact_title": "مسمى المسؤول أو غير مذكورة",
  "contact_channel": "وسيلة الاتصال أو غير مذكورة",
  "cr_status": "متوفر أو غير متوفر أو غير واضح",
  "cr_number": "رقم السجل إن وجد أو null",
  "exact_requirement": "نص ووصف الاحتياج التفصيلي",
  "requested_deadline_text": "الموعد المطلوب كنص",
  "requested_deadline_days": 12,
  "primary_service_name": "اسم الخدمة الأساسية من الدليل أو خارج النطاق أو غير محدد / يتطلب استيضاح",
  "secondary_service_name": "اسم الخدمة الثانوية إن وجدت أو لا توجد",
  "policy_evaluation": "متوافق أو عاجل ويتطلب موافقة أو مخالف أو خارج النطاق أو مخالف وغير مكتمل",
  "is_urgent": false,
  "is_out_of_scope": false,
  "missing_data": ["قائمة الحقول والبيانات الناقصة إن وجدت"],
  "critical_alerts": ["قائمة التنبيهات والقيود والسياسات واجبة المراعاة"],
  "suggested_next_step": "الخطوة التالية الموصى بها تشغيلياً",
  "internal_summary": "نص الملخص الداخلي الموحد بصيغة 04_Output_Template",
  "customer_draft_subject": "عنوان البريد الموجه للعميل",
  "customer_draft_body": "نص الرسالة والرد المهني الموجه للعميل"
}
"""

class DeepSeekLLMEngine:
    """
    Client for Dahl DeepSeek V4 Flash Inference API.
    """

    def __init__(self, api_key: str = DEEPSEEK_API_KEY, endpoint: str = DEEPSEEK_API_URL, model: str = DEEPSEEK_MODEL):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model

    def is_available(self) -> bool:
        return bool(self.api_key and self.endpoint)

    def analyze_request(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Calls DeepSeek to perform deep contextual analysis on customer request text.
        """
        if not self.is_available() or not raw_text.strip():
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        user_content = f"نص طلب العميل الوارد للمعالجة:\n\"\"\"\n{raw_text}\n\"\"\"\n\nقم بالتحليل واستخراج الكيانات وتطبيق السياسات وإرجاع الـ JSON المطلوب بدقة عالية."

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_ANALYZE},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                
                # Extract JSON if enclosed in markdown code blocks
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                parsed = json.loads(content)
                return parsed
        except Exception as e:
            print(f"[DeepSeekLLMEngine] Error during request analysis: {e}")
            return None

    def chat(self, messages: List[Dict[str, str]], context: str = "") -> str:
        """
        Interactive multi-turn conversation with DeepSeek about requests, policies, or catalogs.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        sys_msg = (
            "أنت المساعد الاستشاري الذكي وخبير العمليات لشركة هورايزون لخدمات الأعمال (Horizon B2B Services).\n"
            "الخدمات الثمانية المعتمدة حصراً لدى هورايزون هي:\n"
            "1. الاستشارات الإدارية والتحول التشغيلي (10-15 يوم عمل)\n"
            "2. أتمتة العمليات والحلول الذكية (5-10 أيام عمل)\n"
            "3. تطوير التطبيقات والحلول الرقمية (15-30 يوم عمل)\n"
            "4. البنية التحتية السحابية والأمن السيبراني (7-14 يوم عمل)\n"
            "5. تحليل البيانات ولوحات ذكاء الأعمال (5-12 يوم عمل)\n"
            "6. التدريب وبناء القدرات المؤسسية (3-7 أيام عمل)\n"
            "7. التكامل والربط بين الأنظمة (7-15 يوم عمل)\n"
            "8. الدعم الفني وإدارة الأنظمة (اشتراك شهري/ربع سنوي)\n\n"
            "سياسات التشغيل الصارمة:\n"
            "- السجل التجاري إلزامي (سياسة 1)\n"
            "- الحد الأدنى لأي عمل 3 أيام عمل (سياسة 2)\n"
            "- المواعيد المستعجلة تتطلب موافقة COO وتسعير استعجال (سياسة 3)\n"
            "- اكتمال بيانات الاتصال إلزامي (سياسة 4)\n"
            "- التسويق الرقمي وإدارة حسابات التواصل والإعلانات خارج النطاق ويُعتذر عنها بلباقة (سياسة 5)\n"
            "- تحديد الخدمة الأساسية والثانوية عند تعدد المهام (سياسة 6)\n"
            "- منع الوعود المجانية والخصومات غير المعتمدة (سياسة 7)\n"
            "- المراجعة البشرية الإلزامية لكافة المخرجات (سياسة 8)\n\n"
            "أنت تجيب بلباقة واحترافية وتساعد موظف العمليات في مراجعة الطلبات وصياغة الردود بدقة."
        )
        if context:
            sys_msg += f"\n\nالسياق الحالي للطلب قيد المناقشة:\n{context}"

        full_messages = [{"role": "system", "content": sys_msg}] + messages

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": 0.2
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"خطأ من الخادم (رمز {resp.status_code}): {resp.text}"
        except Exception as e:
            return f"تعذر الاتصال بنموذج DeepSeek: {str(e)}"
