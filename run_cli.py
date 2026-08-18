"""
Horizon B2B Services - Interactive Command Line Tool
أداة سطر الأوامر لمعالجة الطلبات وتوليد الملخصات الموحدة
"""

import sys
import os
import argparse

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from horizon_ai.ai_workflow import HorizonAIWorkflow
from horizon_ai.file_parser import FileParser
from horizon_ai.database import RequestDatabase

def main():
    parser = argparse.ArgumentParser(description="Horizon B2B Services AI Workflow CLI")
    parser.add_argument("--sample", "-s", choices=['A', 'B', 'C', 'D', 'E'], help="تشغيل أحد النماذج المعتمدة (A - E)")
    parser.add_argument("--file", "-f", help="مسار ملف الطلب (TXT, PDF, DOCX, JSON)")
    parser.add_argument("--text", "-t", help="نص الطلب المباشر")
    parser.add_argument("--export", "-e", choices=['excel', 'csv', 'json'], help="تصدير السجلات إلى ملف")
    parser.add_argument("--output", "-o", default="output_summary.txt", help="مسار حفظ المخرج النصي")

    args = parser.parse_args()
    workflow = HorizonAIWorkflow()

    text_to_process = ""
    source_filename = None

    if args.sample:
        base_dir = os.path.join(os.path.dirname(__file__), "Package_Files-20260818T104518Z-1-001", "Package_Files")
        fname = f"0{5 + ord(args.sample) - ord('A')}_Request_{args.sample}.txt"
        path = os.path.join(base_dir, fname)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                text_to_process = f.read()
            source_filename = fname
        else:
            print(f"[!] ملف العينة {fname} غير موجود.")
            sys.exit(1)
    elif args.file:
        if not os.path.exists(args.file):
            print(f"[!] الملف {args.file} غير موجود.")
            sys.exit(1)
        with open(args.file, 'rb') as f:
            raw_bytes = f.read()
        extracted, err = FileParser.parse_file(args.file, raw_bytes)
        if err:
            print(f"[!] خطأ في قراءة الملف: {err}")
            sys.exit(1)
        text_to_process = extracted
        source_filename = os.path.basename(args.file)
    elif args.text:
        text_to_process = args.text
    elif args.export:
        db = RequestDatabase()
        records = db.get_all_requests(limit=1000)
        from horizon_ai.exporters import DataExporter
        exporter = DataExporter()
        if args.export == 'excel':
            b = exporter.export_to_excel_bytes(records)
            with open("Horizon_Report.xlsx", "wb") as f:
                f.write(b)
            print("[✓] تم تصدير السجلات بنجاح إلى: Horizon_Report.xlsx")
        elif args.export == 'csv':
            c = exporter.export_to_csv(records)
            with open("Horizon_Report.csv", "w", encoding="utf-8-sig") as f:
                f.write(c)
            print("[✓] تم تصدير السجلات بنجاح إلى: Horizon_Report.csv")
        elif args.export == 'json':
            j = exporter.export_to_json(records)
            with open("Horizon_Report.json", "w", encoding="utf-8") as f:
                f.write(j)
            print("[✓] تم تصدير السجلات بنجاح إلى: Horizon_Report.json")
        sys.exit(0)
    else:
        print("[!] الرجاء تحديد خيار: --sample A أو --file path/to/file.txt أو --text '...' أو --export excel")
        sys.exit(1)

    print("=" * 70)
    print("  [+] جاري تشغيل خط سير العمل الذكي (AI Workflow)...")
    print("=" * 70)

    result = workflow.process_request(
        raw_text=text_to_process,
        source_filename=source_filename,
        save_to_db=True
    )

    print(result["internal_summary"])
    print("\n" + "=" * 70)
    print("  [✓] مسودة الرد المقترحة للعميل:")
    print("=" * 70)
    print(f"الموضوع: {result['customer_draft_subject']}\n")
    print(result['customer_draft_body'])

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result["internal_summary"] + "\n\n" + "-"*50 + "\n\n" + result["customer_draft_body"])
    print(f"\n[✓] تم حفظ المخرج في الملف: {args.output}")

if __name__ == "__main__":
    main()
