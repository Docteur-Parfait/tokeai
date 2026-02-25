"""
Validate that extracted content looks like an article before sending to Gemini.
Raises ExtractionError with a user-friendly message when content is not article-like
(e.g. 404 page, login page, invoice, form).
"""

import re

from src.logging_config.json_logger import get_logger
from src.utils.exceptions import ExtractionError

# Minimum length and word count to consider content as article-like
MIN_CHARS = 100
MIN_WORDS = 20

# For PDF: minimum ratio of letters (a-z, A-Z) to total non-space chars to consider as article
MIN_ALPHA_RATIO = 0.4

# Phrases that indicate the URL is not an article (error page, login, etc.)
URL_NON_ARTICLE_PHRASES = [
    "404",
    "page not found",
    "access denied",
    "log in",
    "login",
    "sign in",
    "signin",
]

logger = get_logger("utils.content_validation")


def validate_article_content(text: str, source: str = "url") -> None:
    """
    Raise ExtractionError if the extracted text does not look like an article.
    :param text: Extracted plain text (from URL or PDF).
    :param source: "url" or "pdf" for tailored error messages and rules.
    :raises ExtractionError: When content is too short, or URL looks like error/login, or PDF is not article-like.
    """
    if not text or not text.strip():
        if source == "url":
            raise ExtractionError("This link doesn't appear to point to an article. Please use a link to a readable article.")
        raise ExtractionError("This PDF doesn't appear to contain an article. Please upload a document with article-like content (e.g. text with paragraphs).")
    t = text.strip()
    # Minimum length and word count
    words = t.split()
    if len(t) < MIN_CHARS or len(words) < MIN_WORDS:
        logger.warning(
            "Content too short for article",
            extra={"action_type": "content_validation", "source": source, "chars": len(t), "words": len(words)},
        )
        if source == "url":
            raise ExtractionError("This link doesn't appear to point to an article. Please use a link to a readable article.")
        raise ExtractionError("This PDF doesn't appear to contain an article. Please upload a document with article-like content (e.g. text with paragraphs).")
    # URL-specific: detect error/login pages
    if source == "url":
        lower = t.lower()
        for phrase in URL_NON_ARTICLE_PHRASES:
            if phrase in lower:
                logger.warning(
                    "URL content looks like non-article page",
                    extra={"action_type": "content_validation", "source": source, "phrase": phrase},
                )
                raise ExtractionError("This link doesn't appear to point to an article. Please use a link to a readable article.")
    # PDF-specific: reject if mostly numbers/symbols (e.g. invoice, form)
    if source == "pdf":
        non_space = re.sub(r"\s+", "", t)
        if not non_space:
            raise ExtractionError("This PDF doesn't appear to contain an article. Please upload a document with article-like content (e.g. text with paragraphs).")
        alpha = sum(1 for c in non_space if c.isalpha())
        ratio = alpha / len(non_space)
        if ratio < MIN_ALPHA_RATIO:
            logger.warning(
                "PDF content has low letter ratio (not article-like)",
                extra={"action_type": "content_validation", "source": source, "alpha_ratio": round(ratio, 2)},
            )
            raise ExtractionError("This PDF doesn't appear to contain an article. Please upload a document with article-like content (e.g. text with paragraphs).")
