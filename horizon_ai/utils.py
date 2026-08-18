"""
Horizon B2B Services - Arabic Text Utilities & Normalization
أدوات معالجة وتطبيع النصوص العربية وإزالة التشكيل والزوائد
"""

import re

# Arabic diacritics regex
ARABIC_DIACRITICS_REGEX = re.compile(r'[\u064B-\u065F\u0670\u0617-\u061A\u06D6-\u06ED]')

def normalize_arabic(text: str) -> str:
    """
    Normalizes Arabic text for high-precision semantic & keyword matching:
    - Removes all diacritics and tanween (ً ٌ ٍ َ ُ ِ ّ ْ)
    - Normalizes Alef variants (أ, إ, آ, ٱ -> ا)
    - Normalizes Taa Marbuta (ة -> ه)
    - Normalizes Alef Maksura (ى -> ي)
    - Normalizes Tatweel / Kashida (ـ)
    - Normalizes multiple spaces
    """
    if not text:
        return ""

    # Remove diacritics
    text = ARABIC_DIACRITICS_REGEX.sub('', text)

    # Remove tatweel
    text = text.replace('ـ', '')

    # Normalize Alef forms
    text = re.sub(r'[أإآٱ]', 'ا', text)

    # Normalize Alef Maksura & Yaa
    text = text.replace('ى', 'ي')

    # Normalize Taa Marbuta
    text = text.replace('ة', 'ه')

    # Collapse multiple whitespaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def contains_arabic_phrase(text: str, phrase: str) -> bool:
    """
    Checks if normalized text contains normalized phrase.
    """
    norm_text = normalize_arabic(text)
    norm_phrase = normalize_arabic(phrase)
    return norm_phrase in norm_text
