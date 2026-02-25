"""
Extract plain text from a PDF file (bytes or file-like).
Uses pypdf; raises ExtractionError on failure and logs success/error in JSON.
"""

import io
from typing import BinaryIO

from pypdf import PdfReader

from src.logging_config.json_logger import get_logger
from src.utils.exceptions import ExtractionError
from src.utils.content_validation import validate_article_content

# Limits to avoid excessive memory and API usage
MAX_PAGES = 500
MAX_TEXT_LEN = 1_500_000  # ~500k tokens equivalent as rough limit

logger = get_logger("extractors.pdf")


def extract_text_from_pdf(source: bytes | BinaryIO) -> str:
    """
    Extract text from all pages of the PDF.
    :param source: PDF content as bytes or a file-like object (e.g. Streamlit UploadedFile).
    :return: Concatenated text from all pages.
    :raises ExtractionError: If PDF is invalid, empty, too large, or unreadable (e.g. scanned without OCR).
    """
    try:
        if isinstance(source, bytes):
            stream = io.BytesIO(source)
        else:
            stream = source
        reader = PdfReader(stream)
        num_pages = len(reader.pages)
        if num_pages > MAX_PAGES:
            logger.warning(
                "PDF page limit exceeded",
                extra={"action_type": "extraction_pdf", "pages": num_pages, "limit": MAX_PAGES},
            )
            raise ExtractionError(f"PDF has too many pages (max {MAX_PAGES}).")
        if num_pages == 0:
            logger.warning("PDF has no pages", extra={"action_type": "extraction_pdf"})
            raise ExtractionError("PDF has no pages.")
        parts = []
        for i in range(num_pages):
            page = reader.pages[i]
            text = page.extract_text() or ""
            parts.append(text)
        full_text = "\n\n".join(parts).strip()
        if len(full_text) > MAX_TEXT_LEN:
            logger.warning(
                "PDF text length exceeded",
                extra={"action_type": "extraction_pdf", "length": len(full_text), "limit": MAX_TEXT_LEN},
            )
            raise ExtractionError(f"Extracted text is too long (max {MAX_TEXT_LEN} characters).")
        if not full_text:
            logger.warning("No text extracted from PDF (e.g. scanned images)", extra={"action_type": "extraction_pdf"})
            raise ExtractionError("No text could be extracted from the PDF. It may be scanned images only.")
        # Ensure content looks like an article (reject invoices, forms, etc.)
        validate_article_content(full_text, source="pdf")
        logger.info(
            "PDF extraction success",
            extra={"action_type": "extraction_pdf", "pages": num_pages, "text_length": len(full_text)},
        )
        return full_text
    except ExtractionError:
        raise
    except Exception as e:
        logger.exception(
            "PDF extraction failed",
            extra={"action_type": "extraction_pdf", "error": str(e)},
        )
        raise ExtractionError(f"Failed to read PDF: {e!s}.") from e
