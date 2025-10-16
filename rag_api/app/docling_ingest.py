import logging
import os
from pathlib import Path
from typing import List

from pypdf import PdfReader

logger = logging.getLogger(__name__)


def _extract_text_with_docling(file_path: str) -> str:
    try:
        # Heuristic import to support different docling package structures
        try:
            from docling.document_converter import DocumentConverter  # type: ignore
            converter = DocumentConverter()
            doc = converter.convert(file_path)
            if hasattr(doc, "document") and hasattr(doc.document, "export_to_text"):
                return doc.document.export_to_text()
            if hasattr(doc, "export_to_text"):
                return doc.export_to_text()  # type: ignore[attr-defined]
        except Exception:
            # Fallback generic import namespace
            import docling  # type: ignore
            if hasattr(docling, "DocumentConverter"):
                converter = docling.DocumentConverter()  # type: ignore[attr-defined]
                doc = converter.convert(file_path)
                if hasattr(doc, "export_to_text"):
                    return doc.export_to_text()  # type: ignore[attr-defined]
        raise RuntimeError("Docling parse failed or export method not found")
    except Exception as e:
        logger.warning("Docling failed for %s: %s", file_path, e)
        raise


def _extract_text_fallback(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        try:
            reader = PdfReader(file_path)
            texts = [page.extract_text() or "" for page in reader.pages]
            return "\n\n".join(texts)
        except Exception as e:
            logger.warning("PDF fallback parse failed for %s: %s", file_path, e)
    # Plain text fallback
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logger.error("Could not read file %s: %s", file_path, e)
        return ""


def extract_text(file_path: str, prefer_docling: bool = True) -> str:
    if prefer_docling:
        try:
            return _extract_text_with_docling(file_path)
        except Exception:
            return _extract_text_fallback(file_path)
    return _extract_text_fallback(file_path)
