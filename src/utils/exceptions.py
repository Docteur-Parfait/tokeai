"""
Custom exceptions for TokeAI.
Used by extractors and Gemini service; caught in UI for user-friendly messages.
"""


class ExtractionError(Exception):
    """Raised when content extraction from URL or PDF fails."""

    pass


class GeminiServiceError(Exception):
    """Raised when the Gemini API call fails (key, quota, timeout, etc.)."""

    pass
