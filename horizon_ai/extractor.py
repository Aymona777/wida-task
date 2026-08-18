"""
Horizon B2B Services - Arabic Entity & Request Extractor
محرك استخراج الكيانات والبيانات من طلبات العملاء باللغة العربية
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from .utils import normalize_arabic

@dataclass
class ExtractedRequestData:
    organization_name: str = "غير مذكور"
    contact_person: str = "غير مذكور"
    contact_title: str = "غير مذكورة"
    contact_full: str = "غير مذكور"
    contact_channel: str = "غير مذكورة"
    email: Optional[str] = None
    phone: Optional[str] = None
    cr_raw: str = "غير مذكور"
    cr_status: str = "غير متوفر"
    cr_number: Optional[str] = None
    exact_requirement: str = ""
    requirement_summary: str = ""
    requested_deadline_text: str = "غير محدد"
    requested_deadline_days: Optional[int] = None
    is_deadline_urgent_text: bool = False
    requested_discount_or_free: bool = False
    missing_fields: List[str] = field(default_factory=list)
    raw_text: str = ""

class RequestExtractor:
    """
    Intelligent Arabic Entity and Requirement Extractor.
    Robustly handles key-value lines, narrative paragraphs, email headers, and mixed formats.
    """

    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    PHONE_REGEX = re.compile(r'(?:\+?966|0)?5\d{8}|\b05\d{8}\b|\b01\d{7}\b|\b\d{10}\b')
    CR_NUM_REGEX = re.compile(r'\b(?:\d{10})\b')
    DAYS_REGEX = re.compile(r'(\d+)\s*(?:يوم|أيام|ايام|أيام عمل|ايام عمل|يوم عمل)')

    def __init__(self):
        pass

    def extract(self, text: str) -> ExtractedRequestData:
        if not text or not text.strip():
            return ExtractedRequestData(
                missing_fields=[
                    "اسم الجهة", "اسم شخص التواصل وصفته", "وسيلة التواصل",
                    "وصف الاحتياج", "الموعد المطلوب", "السجل التجاري الساري"
                ],
                raw_text=""
            )

        cleaned_text = text.strip()
        result = ExtractedRequestData(raw_text=cleaned_text)

        # 1. Narrative & Explicit Extraction
        org_name, person, title = self._extract_org_and_contact(cleaned_text)
        result.organization_name = org_name
        result.contact_person = person
        result.contact_title = title
        if title != "غير مذكورة" and person != "غير مذكور":
            result.contact_full = f"{person} - {title}"
        elif person != "غير مذكور":
            result.contact_full = person
        else:
            result.contact_full = "غير مذكور"

        # 2. Extract Channels
        channel_str, email, phone = self._extract_channels(cleaned_text)
        result.contact_channel = channel_str
        result.email = email
        result.phone = phone

        # 3. Extract Commercial Registration
        cr_raw, cr_status, cr_num = self._extract_commercial_registration(cleaned_text)
        result.cr_raw = cr_raw
        result.cr_status = cr_status
        result.cr_number = cr_num

        # 4. Extract Exact Requirement
        exact_req, req_summary = self._extract_requirement(cleaned_text)
        result.exact_requirement = exact_req
        result.requirement_summary = req_summary

        # 5. Extract Desired Deadline
        deadline_text, deadline_days, is_vague = self._extract_deadline(cleaned_text)
        result.requested_deadline_text = deadline_text
        result.requested_deadline_days = deadline_days

        # 6. Check Discount or Free Mentions
        result.requested_discount_or_free = self._check_discount_or_free_mention(cleaned_text)

        # 7. Evaluate Missing Fields
        result.missing_fields = self._evaluate_missing_fields(result)

        return result

    def _extract_org_and_contact(self, text: str) -> Tuple[str, str, str]:
        """
        Syntactic Arabic analysis for Organization Name, Contact Person and Title.
        Handles both structured fields and natural narrative introductions.
        """
        org_name = "غير مذكور"
        person = "غير مذكور"
        title = "غير مذكورة"

        # Pattern 1: Narrative introductory sentence
        # Example: "أنا نورة السالم، مديرة التخطيط في شركة روافد التجزئة الافتراضية."
        # Example: "أنا فهد المنصور، مدير التشغيل في مجموعة البناء الحديث للتطوير العقاري."
        # Example: "معكم خالد التميمي من شركة مسارات التموين."
        intro_match = re.search(
            r'(?:أنا|معكم|اسمي|معكم الأخ|معكم الأستاذ|معكم الدكتور|معكم المهندس)\s+([^\n\r،,.]+?)(?:[،,]\s*([^\n\r،,.]+?))?\s+(?:في|من|لدى)\s+([^\n\r،,.]+)',
            text
        )
        if intro_match:
            raw_person = intro_match.group(1).strip()
            raw_title = intro_match.group(2).strip() if intro_match.group(2) else None
            raw_org = intro_match.group(3).strip()

            # Clean particles
            raw_person = re.sub(r'^(?:أنا|معكم|الأخ|الأستاذ|المهندس|الدكتور|د\.)\s*', '', raw_person).strip()
            if raw_person:
                person = raw_person

            if raw_title:
                title = raw_title

            if raw_org:
                org_name = raw_org

        # Pattern 2: "نحن مصنع المدار..." or "نحن شركة..."
        if org_name == "غير مذكور":
            we_match = re.search(r'(?:نحن|نحن في)\s+((?:شركة|مصنع|مؤسسة|مجموعة|هيئة|مركز)\s+[^\n\r،,.(]+)', text)
            if we_match:
                org_name = we_match.group(1).strip()

        # Pattern 3: Explicit Labels for Organization
        lbl_org = re.search(r'(?:اسم الجهة|الجهة|الشركة|اسم الشركة|المنشأة|المؤسسة|العميل)\s*:\s*([^\n\r\t]+)', text)
        if lbl_org:
            v = lbl_org.group(1).strip()
            v = re.sub(r'^[-\s*#]+', '', v)
            if v and v not in ["غير محددة", "غير معروف", "غير مذكور", "مجهول", "جهة غير محددة", "-"]:
                org_name = v

        # Pattern 4: Explicit Labels for Contact Person & Title
        lbl_contact = re.search(r'(?:شخص التواصل|مسؤول التواصل|المسؤول|اسم المسؤول|المتواصل|جهة الاتصال|المرسل)\s*:\s*([^\n\r\t]+)', text)
        if lbl_contact:
            raw_val = lbl_contact.group(1).strip()
            if raw_val and raw_val not in ["غير مذكور", "غير معروف", "-", "لا يوجد"]:
                # Check for hyphen separation (e.g. "فهد العتيبي - مدير التسويق")
                if "-" in raw_val:
                    parts = [p.strip() for p in raw_val.split("-", 1)]
                    person = parts[0]
                    if len(parts) > 1 and parts[1]:
                        title = parts[1]
                elif "–" in raw_val:
                    parts = [p.strip() for p in raw_val.split("–", 1)]
                    person = parts[0]
                    if len(parts) > 1 and parts[1]:
                        title = parts[1]
                elif "،" in raw_val:
                    parts = [p.strip() for p in raw_val.split("،", 1)]
                    person = parts[0]
                    if len(parts) > 1 and parts[1]:
                        title = parts[1]
                else:
                    person = raw_val

        # Fallback check for single person name if still missing
        if person == "غير مذكور":
            single_person = re.search(r'(?:أنا|معكم)\s+([^\n\r،,.]+)', text)
            if single_person and "شركة" not in single_person.group(1) and "مصنع" not in single_person.group(1):
                clean_p = re.sub(r'^(?:أنا|معكم|الأستاذ|المهندس)\s*', '', single_person.group(1)).strip()
                if len(clean_p) > 2 and len(clean_p.split()) <= 4:
                    person = clean_p

        # Fallback check for organization mention anywhere in narrative
        if org_name == "غير مذكور":
            org_fallback = re.search(r'(?:شركة|مصنع|مؤسسة|مجموعة|هيئة|مركز)\s+([^\n\r،,.)]+)', text)
            if org_fallback:
                val = org_fallback.group(0).strip()
                # filter out horizon itself
                if "هورايزون" not in val and "Horizon" not in val:
                    org_name = val

        return org_name, person, title

    def _extract_channels(self, text: str) -> Tuple[str, Optional[str], Optional[str]]:
        emails = self.EMAIL_REGEX.findall(text)
        phones = self.PHONE_REGEX.findall(text)

        # Filter out CR numbers mistakenly matched as phones (10 digits starting with 99 or 70)
        valid_phones = []
        for p in phones:
            p_clean = p.strip()
            if p_clean.startswith('05') or p_clean.startswith('+966') or p_clean.startswith('966'):
                valid_phones.append(p_clean)
            elif len(p_clean) == 10 and not p_clean.startswith('99') and not p_clean.startswith('70'):
                valid_phones.append(p_clean)

        email = emails[0] if emails else None
        phone = valid_phones[0] if valid_phones else None

        # Check explicit label
        m = re.search(r'(?:وسيلة التواصل|بيانات التواصل|وسائل الاتصال|البريد والاتصال|معلومات الاتصال)\s*:\s*([^\n\r\t]+)', text)
        if m:
            val = m.group(1).strip()
            # Clean "البريد:" or "الهاتف:" prefixes inside the label
            val = re.sub(r'^(?:البريد|الهاتف|جوال)\s*:\s*', '', val).strip()
            if "غير مذكورة" in val or "غير مذكور" in val or val in ["-", "لا يوجد"]:
                return "غير مذكورة", email, phone
            return val, email, phone

        if email and phone:
            return f"{email} | {phone}", email, phone
        elif email:
            return email, email, phone
        elif phone:
            return phone, email, phone

        return "غير مذكورة", None, None

    def _extract_commercial_registration(self, text: str) -> Tuple[str, str, Optional[str]]:
        # Check label "السجل التجاري:"
        m = re.search(r'(?:السجل التجاري|رقم السجل التجاري|السجل|سجل تجاري)\s*:\s*([^\n\r\t)]+)', text)
        if m:
            val = m.group(1).strip()
            num_match = self.CR_NUM_REGEX.search(val)
            if num_match:
                return f"متوفر (سجل رقم {num_match.group(0)})", "متوفر", num_match.group(0)
            
            digit_m = re.search(r'\d+', val)
            if digit_m:
                return f"متوفر (سجل رقم {digit_m.group(0)})", "متوفر", digit_m.group(0)

            if any(w in val for w in ["غير مرفق", "غير متوفر", "غير مذكور", "لا يوجد", "بدون سجل"]):
                return "غير متوفر", "غير متوفر", None

            if "غير واضح" in val:
                return "غير واضح", "غير واضح", None

            return val, "متوفر", None

        # Search anywhere in text for 10-digit number preceded by سجل
        any_cr = re.search(r'(?:سجل|سجل تجاري)\s*(?:رقم|:)?\s*(\d{8,12})', text)
        if any_cr:
            return f"متوفر (سجل رقم {any_cr.group(1)})", "متوفر", any_cr.group(1)

        return "غير متوفر", "غير متوفر", None

    def _extract_requirement(self, text: str) -> Tuple[str, str]:
        # Check explicit label
        m = re.search(r'(?:الاحتياج|نص الطلب|المطلوب|تفاصيل الطلب|وصف الاحتياج|الطلب)\s*:\s*([\s\S]+?)(?=(?:\n[^\n:]+:|$))', text)
        if m:
            req = m.group(1).strip()
            lines = req.split('\n')
            clean_lines = []
            for l in lines:
                l_str = l.strip()
                if re.match(r'^(?:الموعد المطلوب|السجل التجاري|وسيلة التواصل|الجهة|شخص التواصل)\s*:', l_str):
                    break
                clean_lines.append(l_str)
            
            full_req = " ".join([cl for cl in clean_lines if cl])
            return full_req, full_req

        # Narrative cleanup (strip greetings, contacts, CR)
        lines = [l.strip() for l in text.split('\n') if l.strip() and not l.startswith('=') and not l.startswith('طلب عميل')]
        req_lines = []
        for l in lines:
            if re.match(r'^(?:الجهة|شخص التواصل|مسؤول التواصل|وسيلة التواصل|بيانات التواصل|البريد|الهاتف|جوال|الموعد المطلوب|السجل التجاري|رقم السجل)\s*:', l):
                continue
            if l.startswith('السلام عليكم') or l.startswith('مرحباً') or l.startswith('تحية طيبة') or l.startswith('شاكرين') or l.startswith('بانتظار'):
                continue
            req_lines.append(l)

        if req_lines:
            combined = " ".join(req_lines)
            return combined, combined

        return text.strip(), text.strip()

    def _extract_deadline(self, text: str) -> Tuple[str, Optional[int], bool]:
        def parse_days_from_str(val_str: str) -> Optional[int]:
            d_m = re.search(r'(\d+)', val_str)
            if d_m:
                return int(d_m.group(1))
            val_clean = val_str.strip()
            if "يومين" in val_clean or "يومان" in val_clean:
                return 2
            elif "يوم واحد" in val_clean or "خلال يوم" in val_clean:
                return 1
            elif "ثلاثة ايام" in val_clean or "ثلاثة أيام" in val_clean or "ثلاث ايام" in val_clean:
                return 3
            elif "اربعة ايام" in val_clean or "أربعة أيام" in val_clean or "اربع ايام" in val_clean:
                return 4
            elif "خمسة ايام" in val_clean or "خمسة أيام" in val_clean or "خمس ايام" in val_clean:
                return 5
            elif "ستة ايام" in val_clean or "ستة أيام" in val_clean or "ست ايام" in val_clean:
                return 6
            elif "سبعة ايام" in val_clean or "سبعة أيام" in val_clean:
                return 7
            elif "ثمانية ايام" in val_clean or "ثمانية أيام" in val_clean:
                return 8
            elif "تسعة ايام" in val_clean or "تسعة أيام" in val_clean:
                return 9
            elif "عشرة ايام" in val_clean or "عشرة أيام" in val_clean:
                return 10
            elif "اسبوعين" in val_clean or "أسبوعين" in val_clean:
                return 10
            elif "اسبوع" in val_clean or "أسبوع" in val_clean:
                return 5
            elif "شهرين" in val_clean:
                return 40
            elif "شهر" in val_clean:
                return 20
            return None

        # Search label "الموعد المطلوب:"
        m = re.search(r'(?:الموعد المطلوب|الموعد المحدد|تاريخ التسليم|المدة المطلوبة|موعد التسليم|الموعد)\s*:\s*([^\n\r\t]+)', text)
        if m:
            val = m.group(1).strip()
            days = parse_days_from_str(val)
            if days is not None:
                return val, days, False
            if any(w in val for w in ["قريب", "بأسرع وقت", "عاجل", "فوري"]):
                return val, None, True
            return val, None, True

        # Search narrative "خلال X يوم عمل"
        narrative_days = re.search(r'(?:خلال|في غضون|خلال مدة|لمدة)\s*(\d+)\s*(?:يوم عمل|ايام عمل|أيام عمل|يوم|أيام|ايام)', text)
        if narrative_days:
            days = int(narrative_days.group(1))
            return f"خلال {days} يوم عمل", days, False

        # Search "الوقت المستهدف لبدء التشغيل التجريبي هو X أيام عمل"
        target_days = re.search(r'(?:الوقت المستهدف|الموعد المستهدف|التشغيل التجريبي هو)\s*(\d+)\s*(?:يوم عمل|ايام عمل|أيام عمل|يوم|أيام|ايام)', text)
        if target_days:
            days = int(target_days.group(1))
            return f"خلال {days} أيام عمل", days, False

        # Search "لمدة X أشهر"
        months_match = re.search(r'(?:مطلع الشهر القادم ولمدة|لمدة)\s*(\d+)\s*أشهر', text)
        if months_match:
            months = int(months_match.group(1))
            return f"مطلع الشهر القادم ولمدة {months} أشهر", months * 20, False

        # Textual days
        days_from_text = parse_days_from_str(text)
        if days_from_text is not None:
            return f"خلال {days_from_text} أيام عمل", days_from_text, False

        if "قريب" in text or "بأسرع وقت" in text or "عاجل" in text:
            return "قريباً (غير محدد بدقة)", None, True

        return "غير محدد", None, False

    def _check_discount_or_free_mention(self, text: str) -> bool:
        triggers = [
            "دون تكلفة كبيرة", "بدون تكلفة", "سعر منخفض", "خصم", "مجان",
            "بشكل مجاني", "مجانًا", "تخفيض", "أرخص سعر", "سعر رمزي", "أرخص تكلفة", "تجربة مجانية"
        ]
        return any(t in text for t in triggers)

    def _evaluate_missing_fields(self, data: ExtractedRequestData) -> List[str]:
        missing = []

        if not data.organization_name or data.organization_name in ["غير مذكور", "جهة غير محددة"]:
            missing.append("اسم الجهة / المنشأة")

        if not data.contact_person or data.contact_person == "غير مذكور":
            missing.append("اسم شخص التواصل")

        if not data.contact_title or data.contact_title == "غير مذكورة":
            missing.append("صفة / مسمى شخص التواصل")

        if not data.contact_channel or data.contact_channel == "غير مذكورة" or (not data.email and not data.phone):
            missing.append("وسيلة التواصل (البريد الإلكتروني / رقم الهاتف)")

        if not data.exact_requirement or len(data.exact_requirement) < 15 or "يربط كل شيء" in data.exact_requirement:
            if "يربط كل شيء" in data.exact_requirement:
                missing.append("تفاصيل النطاق الفني والأنظمة المراد التعامل معها (الطلب مبهم وعام)")
            else:
                missing.append("وصف الاحتياج التفصيلي")

        if data.requested_deadline_text in ["غير محدد", "غير مذكور"] or data.requested_deadline_days is None:
            missing.append("تحديد موعد زمني دقيق للتسليم بالأيام")

        if data.cr_status in ["غير متوفر", "غير واضح"]:
            missing.append("السجل التجاري الساري (شرط إلزامي للبدء في التنفيذ الرسمي وفق سياسة 1)")

        return missing
