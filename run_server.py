"""
Horizon B2B Services - AI Application Launcher
مشغل النظام وخادم الويب لمنصة هورايزون الذكية
"""

import sys
import os
import webbrowser
import threading
import time

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from horizon_ai.server import HorizonServer
from aiohttp import web

def open_browser(url: str, delay: float = 1.0):
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[!] Could not open browser automatically: {e}")

def main():
    port = 8000
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    print("=" * 70)
    print("  شركة هورايزون لخدمات الأعمال (Horizon B2B Services)")
    print("  المنظومة الذكية لمعالجة وتصنيف طلبات العملاء وحوكمة السياسات")
    print("=" * 70)
    print(f"  [+] بدء تشغيل الخادم على الرابط: {url}")
    print(f"  [+] محرك الذكاء الاصطناعي: مفعل (Zero Hallucination + 8 Services)")
    print(f"  [+] بوابة المراجعة البشرية (HITL): جاهزة للاستخدام")
    print(f"  [+] جاري فتح المتصفح تلقائياً...")
    print("=" * 70)

    # Initialize samples if db is empty
    server = HorizonServer(port=port, host=host)
    existing_requests = server.db.get_all_requests(limit=1)
    if not existing_requests:
        print("  [*] تهيئة قاعدة البيانات بالعينات التدريبية الرسمية A - E...")
        for letter in ['A', 'B', 'C', 'D', 'E']:
            if letter in server.samples:
                s = server.samples[letter]
                server.workflow.process_request(
                    raw_text=s["text"],
                    source_type="sample_benchmark",
                    source_filename=s["filename"],
                    request_code=f"REQ-2026-000{ord(letter) - ord('A') + 1}",
                    save_to_db=True
                )
        print("  [✓] تمت تهيئة العينات بنجاح.")

    # Start browser opener thread
    threading.Thread(target=open_browser, args=(url, 1.2), daemon=True).start()

    # Run aiohttp web server
    web.run_app(server.app, host=host, port=port)

if __name__ == "__main__":
    main()
