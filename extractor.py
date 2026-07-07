"""Safe text extraction for uploaded news documents and screenshots."""

from __future__ import annotations

import base64
import html
import io
import re
import zipfile
from pathlib import Path


MAX_FILE_SIZE = 12 * 1024 * 1024


def _clean(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _html_text(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="ignore")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return _clean(text)


def _docx_text(raw: bytes) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(raw))
        return _clean("\n".join(p.text for p in doc.paragraphs))
    except ImportError:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            xml = archive.read("word/document.xml").decode(errors="ignore")
        return _clean(re.sub(r"<[^>]+>", " ", xml))


def _pdf_text(raw: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("PDF support is unavailable in this Python installation.") from exc
    reader = PdfReader(io.BytesIO(raw))
    return _clean("\n".join(page.extract_text() or "" for page in reader.pages[:50]))


def extract_file(filename: str, mime: str, encoded: str) -> dict:
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("The uploaded file data is invalid.") from exc
    if not raw:
        raise ValueError("The uploaded file is empty.")
    if len(raw) > MAX_FILE_SIZE:
        raise ValueError("File is too large. Maximum size is 12 MB.")

    suffix = Path(filename).suffix.lower()
    if mime == "application/pdf" or suffix == ".pdf":
        text, kind = _pdf_text(raw), "PDF document"
    elif suffix == ".docx":
        text, kind = _docx_text(raw), "Word document"
    elif mime in {"text/html", "application/xhtml+xml"} or suffix in {".html", ".htm"}:
        text, kind = _html_text(raw), "Web article"
    elif mime.startswith("text/") or suffix in {".txt", ".md", ".csv"}:
        text, kind = _clean(raw.decode("utf-8", errors="ignore")), "Text document"
    else:
        raise ValueError("Unsupported format. Use PDF, DOCX, TXT, HTML, PNG, JPG, or WEBP.")

    if len(re.findall(r"\b\w+\b", text)) < 8:
        raise ValueError("I couldn't find enough readable text in that file.")
    return {"text": text[:100_000], "kind": kind, "characters": len(text)}
