"""
TokeAI Streamlit app: summarize articles from a link or PDF.
UI in English; chat history and "New chat" like ChatGPT; Parfait as assistant personality.
"""

import re
import sys
from pathlib import Path

# Add project root to Python path so "src" imports work when running: streamlit run src/app.py
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import streamlit as st

from src.extractors import extract_text_from_pdf, extract_text_from_url
from src.logging_config.json_logger import get_logger, setup_logging
from src.services.gemini_service import summarize_with_gemini
from src.utils.exceptions import ExtractionError, GeminiServiceError

# Ensure logging is configured on first run
setup_logging()
logger = get_logger("app")

# Simple URL detection: starts with http(s) and has at least one dot or valid domain
URL_PATTERN = re.compile(r"^https?://\S+", re.IGNORECASE)


def _looks_like_url(text: str) -> bool:
    """Return True if the input looks like a URL."""
    t = (text or "").strip()
    return bool(URL_PATTERN.match(t))


def _init_session_state() -> None:
    """Initialize session state for chat messages if not already set."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def _new_chat() -> None:
    """Clear chat history (New chat action)."""
    st.session_state.messages = []
    logger.info("New chat started", extra={"action_type": "app"})


def _process_url(user_input: str) -> None:
    """Extract content from URL, summarize with Gemini, and append user + assistant messages."""
    try:
        with st.spinner("Fetching and reading the article..."):
            text = extract_text_from_url(user_input)
        with st.spinner("Parfait is summarizing..."):
            summary = summarize_with_gemini(text, source_type="url")
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": summary})
    except ExtractionError as e:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I couldn't use that link: {e!s}"})
    except GeminiServiceError as e:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": str(e)})
    except Exception as e:
        logger.exception("Unexpected error in URL flow", extra={"action_type": "app", "error": str(e)})
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "assistant", "content": "Something went wrong. Please try again."})


def _process_pdf(pdf_bytes: bytes) -> None:
    """Extract text from PDF, summarize with Gemini, and append user + assistant messages."""
    try:
        with st.spinner("Reading the PDF..."):
            text = extract_text_from_pdf(pdf_bytes)
        with st.spinner("Parfait is summarizing..."):
            summary = summarize_with_gemini(text, source_type="pdf")
        st.session_state.messages.append({"role": "user", "content": "[Uploaded a PDF document]"})
        st.session_state.messages.append({"role": "assistant", "content": summary})
    except ExtractionError as e:
        st.session_state.messages.append({"role": "user", "content": "[Uploaded a PDF document]"})
        st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I couldn't read that PDF: {e!s}"})
    except GeminiServiceError as e:
        st.session_state.messages.append({"role": "user", "content": "[Uploaded a PDF document]"})
        st.session_state.messages.append({"role": "assistant", "content": str(e)})
    except Exception as e:
        logger.exception("Unexpected error in PDF flow", extra={"action_type": "app", "error": str(e)})
        st.session_state.messages.append({"role": "user", "content": "[Uploaded a PDF document]"})
        st.session_state.messages.append({"role": "assistant", "content": "Something went wrong. Please try again."})


def render_sidebar() -> None:
    """Sidebar: New chat button and View logs / Back to chat."""
    st.sidebar.title("TokeAI")
    st.sidebar.caption("Summarize articles from a link or PDF. I'm Parfait, your assistant.")
    if st.sidebar.button("New chat", use_container_width=True):
        _new_chat()
        st.rerun()
    st.sidebar.divider()
    view_logs = st.session_state.get("view_logs", False)
    if view_logs:
        if st.sidebar.button("Back to chat", use_container_width=True):
            st.session_state["view_logs"] = False
            st.rerun()
    else:
        if st.sidebar.button("View logs", use_container_width=True):
            st.session_state["view_logs"] = True
            st.rerun()


def render_logs_view() -> None:
    """Full-page view: read JSON log files and display a filterable table."""
    import json
    import pandas as pd
    from src.config import get_logs_dir
    st.title("Application logs")
    st.caption("Filter by level or action type. Logs are read from the logs/ directory.")
    logs_dir = get_logs_dir()
    if not logs_dir.exists():
        st.info("No logs directory yet. Use the app to generate some logs.")
        return
    log_files = sorted(logs_dir.glob("app_*.json"), reverse=True)
    if not log_files:
        st.info("No log files found. Logs will appear here after you use the app.")
        return
    # Build list of log entries from all or selected file
    selected_file = st.selectbox("Log file", options=log_files, format_func=lambda p: p.name)
    level_filter = st.selectbox("Level", options=["ALL", "DEBUG", "INFO", "WARNING", "ERROR"], index=0)
    action_filter = st.selectbox("Action type", options=["ALL", "extraction_url", "extraction_pdf", "gemini_call", "content_validation", "app"], index=0)
    entries = []
    path = logs_dir / selected_file if isinstance(selected_file, str) else selected_file
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if level_filter != "ALL" and obj.get("level") != level_filter:
                    continue
                if action_filter != "ALL" and obj.get("action_type") != action_filter:
                    continue
                entries.append(obj)
            except json.JSONDecodeError:
                continue
    if not entries:
        st.write("No matching log entries.")
        return
    # Show as table: timestamp, level, action_type, message (and maybe extra keys)
    df = pd.DataFrame(entries)
    # Prefer columns: timestamp, level, action_type, message
    cols = [c for c in ["timestamp", "level", "action_type", "message"] if c in df.columns]
    others = [c for c in df.columns if c not in cols]
    df = df[cols + others] if cols else df
    st.dataframe(df, use_container_width=True, height=400)


def render_chat() -> None:
    """Main area: chat history and unified input (link field + PDF button on same row)."""
    st.header("Chat with Parfait")
    st.caption("Paste an article link or import a PDF below, then click Summarize.")
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    # Single text field on top, then upload area same width below
    with st.form("input_form", clear_on_submit=True):
        link_input = st.text_input(
            "Paste article link",
            placeholder="Paste article link here",
            key="link_input",
            label_visibility="collapsed",
        )
        # Upload area below, full width (same as text field)
        pdf_file = st.file_uploader("Import PDF", type=["pdf"], label_visibility="visible")
        submitted = st.form_submit_button("Summarize")
    if submitted:
        if pdf_file is not None:
            # User uploaded a PDF: process it (ignore text input)
            _process_pdf(pdf_file.read())
            st.rerun()
        elif link_input and _looks_like_url(link_input.strip()):
            _process_url(link_input.strip())
            st.rerun()
        elif link_input and link_input.strip():
            # User entered something that is not a URL
            st.session_state.messages.append({"role": "user", "content": link_input.strip()})
            st.session_state.messages.append({
                "role": "assistant",
                "content": "That doesn't look like an article link. Please paste a link starting with http or https, or import a PDF to summarize.",
            })
            st.rerun()
        else:
            # Empty submit: prompt to provide input
            st.session_state.messages.append({"role": "assistant", "content": "Please paste an article link or import a PDF, then click Summarize."})
            st.rerun()


def main() -> None:
    """Entry point: init session state, then render sidebar and Parfaither logs view or chat."""
    _init_session_state()
    render_sidebar()
    if st.session_state.get("view_logs"):
        render_logs_view()
        return
    render_chat()


if __name__ == "__main__":
    logger.info("TokeAI app starting", extra={"action_type": "app"})
    main()
