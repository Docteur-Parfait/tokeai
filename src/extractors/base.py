"""
Common interface for content extractors (URL and PDF).
Both expose a function that returns plain text from a source; callers use the appropriate one.
"""

# No shared base class required: url_extractor.extract_text_from_url and
# pdf_extractor.extract_text_from_pdf are used by the app based on input type.
