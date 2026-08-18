"""
Horizon B2B Services - File Parser & Ingestion
قارئ ومحلل مختلف صيغ الملفات المرفقة (TXT, PDF, DOCX, JSON, CSV)
"""

import io
import json
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

class FileParser:
    """
    Parses various file types into clean Arabic plain text.
    """

    @classmethod
    def parse_file(cls, filename: str, content_bytes: bytes) -> Tuple[str, Optional[str]]:
        """
        Returns (extracted_text, error_message)
        """
        ext = filename.lower().split('.')[-1] if '.' in filename else 'txt'

        try:
            if ext in ['txt', 'log', 'text']:
                return cls._parse_text(content_bytes), None
            elif ext == 'pdf':
                return cls._parse_pdf(content_bytes), None
            elif ext in ['docx', 'doc']:
                return cls._parse_docx(content_bytes), None
            elif ext == 'json':
                return cls._parse_json(content_bytes), None
            elif ext == 'csv':
                return cls._parse_csv(content_bytes), None
            else:
                # Default fallback: try text decoding
                return cls._parse_text(content_bytes), None
        except Exception as e:
            return "", f"فشل قراءة الملف ({filename}): {str(e)}"

    @classmethod
    def _parse_text(cls, content_bytes: bytes) -> str:
        for encoding in ['utf-8', 'utf-8-sig', 'windows-1256', 'latin-1', 'cp1252']:
            try:
                return content_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content_bytes.decode('utf-8', errors='ignore')

    @classmethod
    def _parse_pdf(cls, content_bytes: bytes) -> str:
        if not PYPDF_AVAILABLE:
            raise ImportError("مكتبة pypdf غير متوفرة لمعالجة ملفات PDF.")

        pdf_file = io.BytesIO(content_bytes)
        reader = pypdf.PdfReader(pdf_file)
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        return "\n".join(text_parts).strip()

    @classmethod
    def _parse_docx(cls, content_bytes: bytes) -> str:
        """
        Parses docx using zipfile & XML without external lxml dependencies.
        """
        docx_file = io.BytesIO(content_bytes)
        with zipfile.ZipFile(docx_file) as docx_zip:
            xml_content = docx_zip.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Extract text from w:t elements
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs = []
            for p in tree.findall('.//w:p', namespaces):
                p_text = ''.join([t.text for t in p.findall('.//w:t', namespaces) if t.text])
                if p_text.strip():
                    paragraphs.append(p_text.strip())
            return "\n".join(paragraphs)

    @classmethod
    def _parse_json(cls, content_bytes: bytes) -> str:
        text = cls._parse_text(content_bytes)
        data = json.loads(text)
        if isinstance(data, dict):
            # If JSON has specific keys, flatten nicely
            lines = []
            for k, v in data.items():
                lines.append(f"{k}: {v}")
            return "\n".join(lines)
        return text

    @classmethod
    def _parse_csv(cls, content_bytes: bytes) -> str:
        text = cls._parse_text(content_bytes)
        return text
