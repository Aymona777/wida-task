"""
Horizon B2B Services - Automated Benchmark Runner
أداة تشغيل وفحص الاختبارات المعيارية من سطر الأوامر
"""

import sys
import os
import unittest

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from horizon_ai.test_suite import TestHorizonAIWorkflowComprehensive

def main():
    print("=" * 70)
    print("  شركة هورايزون لخدمات الأعمال - جناح الاختبارات المعيارية الشامل")
    print("  Horizon B2B Services - Comprehensive Automated Benchmark Suite")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestHorizonAIWorkflowComprehensive)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("  [✓] جميع الاختبارات المعيارية الـ 11 اجتيزت بنجاح وبدقة 100%!")
        print("=" * 70)
        sys.exit(0)
    else:
        print(f"  [X] حدثت إخفاقات: {len(result.failures)} إخفاقات، {len(result.errors)} أخطاء.")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()
