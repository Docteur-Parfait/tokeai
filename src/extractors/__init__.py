"""
Content extractors: URL (goose3) and PDF (pypdf).
"""

from src.extractors.pdf_extractor import extract_text_from_pdf
from src.extractors.url_extractor import extract_text_from_url

__all__ = ["extract_text_from_url", "extract_text_from_pdf"]
