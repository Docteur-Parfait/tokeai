"""
Summarize text using Google Gemini with Parfait personality.
Handles long documents by truncation; logs success/failure and raises GeminiServiceError on API errors.
"""

import google.generativeai as genai

from src.config import get_gemini_api_key
from src.logging_config.json_logger import get_logger
from src.utils.exceptions import GeminiServiceError

# Rough token limit for input (Gemini 1.5: 1M; older models ~30k). Truncate beyond this.
MAX_INPUT_CHARS = 120_000  # ~30k tokens

# Parfait: assistant name and personality (creator). Responds in English with clear, structured summaries.
Parfait_SYSTEM_INSTRUCTION = """You are Parfait, a friendly and professional AI assistant created by Parfait.
Your role is to summarize articles and documents clearly and concisely in English.
Always respond in English. Be helpful, accurate, and structured: use short paragraphs or bullet points when appropriate.
When summarizing, capture the main ideas, key facts, and conclusions. Keep a warm but professional tone."""

logger = get_logger("services.gemini")


def summarize_with_gemini(
    text: str,
    source_type: str = "article",
) -> str:
    """
    Send text to Gemini for summarization; return the model's summary.
    :param text: Raw content (from URL or PDF).
    :param source_type: Label for logging only (e.g. "url", "pdf").
    :return: Summary text in English.
    :raises GeminiServiceError: If API key is missing, invalid, or the request fails.
    """
    api_key = get_gemini_api_key()
    if not api_key or not api_key.strip():
        logger.error("Gemini API key not set", extra={"action_type": "gemini_call", "status": "missing_key"})
        raise GeminiServiceError("API key is not configured. Please set GEMINI_API_KEY in your .env file.")
    # Truncate if too long to avoid token limit errors
    if len(text) > MAX_INPUT_CHARS:
        original_len = len(text)
        text = text[:MAX_INPUT_CHARS] + "\n\n[Content truncated for length.]"
        logger.info(
            "Input truncated for Gemini",
            extra={"action_type": "gemini_call", "original_length": original_len, "max_chars": MAX_INPUT_CHARS},
        )
    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel(
            "gemini-3-flash-preview",
            system_instruction=Parfait_SYSTEM_INSTRUCTION,
        )
        prompt = f"""Summarize the following {source_type} content in English. Provide a clear, structured summary with main points and key takeaways.

Content:

{text}"""
        response = model.generate_content(prompt)
        if not response or not response.text:
            logger.warning("Gemini returned empty response", extra={"action_type": "gemini_call"})
            raise GeminiServiceError("The assistant did not return a valid summary. Please try again.")
        summary = response.text.strip()
        logger.info(
            "Gemini summarization success",
            extra={"action_type": "gemini_call", "source_type": source_type, "summary_length": len(summary)},
        )
        return summary
    except GeminiServiceError:
        raise
    except Exception as e:
        err_msg = str(e).lower()
        if "api_key" in err_msg or "invalid" in err_msg or "401" in err_msg:
            user_msg = "Invalid or missing API key. Please check your GEMINI_API_KEY in .env."
        elif "quota" in err_msg or "429" in err_msg:
            user_msg = "Rate limit or quota exceeded. Please try again later."
        elif "timeout" in err_msg or "deadline" in err_msg:
            user_msg = "Request timed out. Please try again."
        else:
            user_msg = "The summarization service is temporarily unavailable. Please try again."
        logger.exception(
            "Gemini summarization failed",
            extra={"action_type": "gemini_call", "source_type": source_type, "error": str(e)},
        )
        raise GeminiServiceError(user_msg) from e
