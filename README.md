# TokeAI

TokeAI is an AI assistant that summarizes articles from a **link** or an uploaded **PDF**. The assistant has a personality and goes by the name **Parfait** (the creator). The app is built with Python, Streamlit, and Google Gemini.

## Features

- **Summarize from URL**: Paste an article link in the chat to get a clear, structured summary in English.
- **Summarize from PDF**: Upload a PDF in the sidebar, then send a message to summarize it.
- **Chat history**: Conversation is kept in the session (like ChatGPT). Use **New chat** to start over.
- **Logs**: All actions (extractions, Gemini calls, errors) are logged in JSON under `logs/`. You can view and filter them in the app via **View logs** in the sidebar.

## Prerequisites

- **Python 3.10+**
- A **Gemini API key** (free at [Google AI Studio](https://aistudio.google.com/app/apikey))

## Installation

1. **Clone the repository** (or download the project):

   ```bash
   cd D:\python\tokeai
   ```

2. **Create and activate a virtual environment**:
   - Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - Windows (cmd):
     ```cmd
     python -m venv venv
     venv\Scripts\activate.bat
     ```
   - Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the API key**:
   - Copy the example env file:
     ```bash
     copy .env.example .env
     ```
   - Edit `.env` and set your Gemini API key:
     ```
     GEMINI_API_KEY=your_actual_api_key_here
     ```

## Running the application

From the project root (with the virtual environment activated):

```bash
streamlit run src/app.py
```

The app opens in your browser (usually at `http://localhost:8501`).

## Usage

1. **Summarize an article from a link**: Paste a URL (e.g. `https://example.com/article`) in the chat input and press Enter. Parfait will fetch the content and return a summary.
2. **Summarize a PDF**: In the sidebar, use **Upload a PDF** to select a file. Then type any message in the chat (e.g. “Summarize”) and send. Parfait will summarize the PDF.
3. **New chat**: Click **New chat** in the sidebar to clear the conversation and start over.
4. **View logs**: Click **View logs** in the sidebar to see application logs (by level and action type). Use **Back to chat** to return to the assistant.

## Logs

- Log files are written under the **`logs/`** directory as `app_YYYYMMDD.json` (one JSON object per line).
- You can open these files directly or use the **View logs** section in the app to filter by:
  - **Level**: DEBUG, INFO, WARNING, ERROR
  - **Action type**: e.g. `extraction_url`, `extraction_pdf`, `gemini_call`, `app`

## Project structure

```
tokeai/
├── .env.example      # Template for .env (copy to .env and set GEMINI_API_KEY)
├── .gitignore
├── README.md
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── src/
│   ├── app.py              # Streamlit entry point
│   ├── config.py           # Loads GEMINI_API_KEY and paths
│   ├── extractors/         # URL (goose3) and PDF (pypdf) extraction
│   ├── services/           # Gemini summarization (Parfait personality)
│   ├── logging_config/     # JSON file logging
│   └── utils/              # Custom exceptions
└── logs/                   # JSON log files (created at runtime)
```

## Troubleshooting

- **"API key is not configured"**: Ensure `.env` exists and contains `GEMINI_API_KEY=...`.
- **"Failed to fetch or extract content from URL"**: The link may be invalid, require login, or the site may block automated access. Try another article.
- **"No text could be extracted from the PDF"**: The PDF may be scanned images only (no OCR). Use a text-based PDF.
- **Rate limit / quota errors**: Wait a moment and try again, or check your Gemini API quota in Google AI Studio.

## License

Use and modify as needed. Author: Parfait.
