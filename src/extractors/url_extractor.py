"""
Extract article content from a URL using goose3.
Raises ExtractionError on failure and logs success/error in JSON.
"""

from goose3 import Goose
from goose3.configuration import Configuration

from src.logging_config.json_logger import get_logger
from src.utils.exceptions import ExtractionError
from src.utils.content_validation import validate_article_content

# Timeout in seconds for fetching the URL
URL_TIMEOUT = 30

logger = get_logger("extractors.url")


def extract_text_from_url(url: str) -> str:
    """
    Fetch the URL and extract main article text (title + cleaned body) using goose3.
    :param url: Full URL (e.g. https://example.com/article).
    :return: Extracted title and body text combined.
    :raises ExtractionError: On timeout, HTTP errors, or empty content.
    """
    if not url or not url.strip():
        logger.warning("Empty URL provided", extra={"action_type": "extraction_url"})
        raise ExtractionError("No URL provided.")
    url = url.strip()
    try:
        config = Configuration()
        config.http_timeout = URL_TIMEOUT
        with Goose(config) as g:
            article = g.extract(url=url)
        title = (article.title or "").strip()
        cleaned = (article.cleaned_text or "").strip()
        if not cleaned and not title:
            logger.warning("No content extracted from URL", extra={"action_type": "extraction_url", "url": url})
            raise ExtractionError("No article content could be extracted from this URL.")
        full_text = f"{title}\n\n{cleaned}".strip() if title else cleaned
        # Ensure content looks like an article (reject 404, login pages, etc.)
        validate_article_content(full_text, source="url")
        logger.info(
            "URL extraction success",
            extra={"action_type": "extraction_url", "url": url, "text_length": len(full_text)},
        )
        return full_text
    except ExtractionError:
        raise
    except Exception as e:
        logger.exception(
            "URL extraction failed",
            extra={"action_type": "extraction_url", "url": url, "error": str(e)},
        )
        raise ExtractionError(f"Failed to fetch or extract content from URL: {e!s}.") from e
