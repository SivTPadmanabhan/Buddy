# Buddy

A good-boy who fetches the right context for your study sessions.

Buddy is a personal RAG (Retrieval-Augmented Generation) system that indexes your Google Drive documents and lets you ask questions about them in natural language. It remembers your conversations across sessions, so follow-up questions just work.

## Architecture

```
Frontend (React + Vite)  -->  Backend (FastAPI)
                                  |
                  +-------+-------+-------+--------+
                  |       |       |       |        |
               Google  Pinecone  Gemini  Super   Tesseract
               Drive   (vectors) (LLM)  memory    (OCR)
```

**Stack:** FastAPI, React + Vite + Tailwind CSS, Pinecone, Google Gemini, Supermemory, Sentence Transformers, Docker

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- **Or** for local development:
  - Python 3.11+
  - Node.js 20+
  - Tesseract OCR (`apt install tesseract-ocr` on Linux, `brew install tesseract` on macOS)

## API Keys Setup

You need accounts (all have free tiers) for:

| Service | Where to get the key |
|---------|---------------------|
| Google Drive | [console.cloud.google.com](https://console.cloud.google.com) — APIs & Services — Credentials (OAuth 2.0, Desktop app) |
| Pinecone | [pinecone.io](https://www.pinecone.io) — API Keys. Create an index named `buddy-index`, dimension `384` |
| Google Gemini | [aistudio.google.com](https://aistudio.google.com) — Get API Key |
| Supermemory *(optional)* | [console.supermemory.ai](https://console.supermemory.ai) — API Keys |

## Setup

1. **Clone and configure environment:**

```bash
git clone <repo-url>
cd buddy
cp .env.example .env
```

2. **Fill in your API keys** in `.env`:

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
PINECONE_API_KEY=your-key
GEMINI_API_KEY=your-key
DRIVE_FOLDER_IDS=folder-id-1,folder-id-2
SUPERMEMORY_API_KEY=your-key          # optional — chat works without it
```

Get `DRIVE_FOLDER_IDS` from the Google Drive URL: `drive.google.com/drive/folders/ABC123` — the ID is `ABC123`. Comma-separate multiple folders.

## Running with Docker

**Development** (with hot reload):

```bash
docker-compose up --build
```

**Production** (optimized builds, no dev volumes):

```bash
docker-compose -f docker-compose.prod.yml up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

## Running Locally

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.2.2
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Usage

1. **Sync your documents** — click the sync button in the header, or let it auto-sync on startup (`SYNC_ON_STARTUP=true`). Buddy pulls files from your Google Drive folders, parses them (PDFs, Word, PowerPoint, Excel, images via OCR), and indexes them in Pinecone.

2. **Ask questions** — type a question in the chat. Buddy retrieves relevant document chunks, combines them with conversation memory, and generates an answer with source citations.

3. **Follow up** — Buddy remembers your conversation history via Supermemory, so questions like "tell me more about that" or "what else?" work naturally.

### Supported File Types

| Type | Method |
|------|--------|
| PDF | pypdf text extraction |
| Word (.docx) | python-docx |
| PowerPoint (.pptx) | python-pptx |
| Excel (.xlsx) | openpyxl |
| Google Docs/Sheets/Slides | Exported via Drive API |
| Images (PNG, JPG) | Tesseract OCR |
| Plain text, CSV, Markdown | Direct read |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service status and connectivity checks |
| `/chat` | POST | Send a question, get a RAG-augmented response with sources |
| `/sync` | POST | Trigger a Google Drive sync |
| `/sync/status` | GET | Check sync state and document count |
| `/usage` | GET | Current usage vs. daily safety limits |

## Safety Limits

Buddy enforces conservative daily limits to stay within free tier quotas:

| Service | Free Tier | Buddy Limit | Configurable Via |
|---------|-----------|-------------|------------------|
| Gemini requests | ~15 RPM | 1,000/day | `GEMINI_DAILY_REQUESTS` |
| Gemini tokens | 1M/day | 500K/day | `GEMINI_DAILY_TOKENS` |
| Pinecone vectors | 100K | 80K | `PINECONE_MAX_VECTORS` |

- Limits checked before every API call
- Warnings logged at 80% usage
- Friendly errors shown when limits hit ("Buddy is resting for today!")
- Daily counters auto-reset at midnight
- Usage tracked in `data/usage.json` (gitignored)

## Security

- **Never commit `.env`** — it contains API keys and secrets. It is listed in `.gitignore`.
- All sensitive data files (`data/drive_token.json`, `data/usage.json`, `data/sync_state.json`) are gitignored via the `data/` rule.
- OAuth tokens are stored locally in `data/drive_token.json`, never transmitted beyond the Google auth flow.
- No API keys are hardcoded anywhere in the codebase — all secrets load from environment variables via Pydantic Settings.

## Running Tests

```bash
cd backend
pytest
```

## Project Structure

```
buddy/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, health endpoint, auto-sync
│   │   ├── config.py            # Pydantic Settings (env validation)
│   │   ├── logging_config.py    # Structured JSON logging (structlog)
│   │   ├── api/
│   │   │   └── chat.py          # /chat, /sync, /usage endpoints
│   │   └── services/
│   │       ├── drive.py         # Google Drive OAuth + file operations
│   │       ├── document.py      # PDF/Word/PowerPoint/Excel parsing + chunking
│   │       ├── ocr.py           # Tesseract OCR wrapper
│   │       ├── embeddings.py    # Sentence Transformers (all-MiniLM-L6-v2)
│   │       ├── vectorstore.py   # Pinecone upsert/search/delete
│   │       ├── gemini.py        # Gemini API client
│   │       ├── rag.py           # RAG orchestration (embed → search → prompt → generate)
│   │       ├── memory.py        # Supermemory conversation memory
│   │       ├── sync.py          # Drive-to-Pinecone sync pipeline
│   │       └── usage.py         # Daily usage tracking + limit enforcement
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Layout, empty state, error banners
│   │   ├── api/
│   │   │   ├── client.ts        # Typed API client with error handling
│   │   │   └── theme.ts         # Dark/light mode manager
│   │   ├── components/
│   │   │   ├── Header.tsx       # Logo, sync button, usage popover, theme toggle
│   │   │   ├── ChatMessage.tsx  # Messages with markdown + expandable sources
│   │   │   ├── ChatInput.tsx    # Auto-resize textarea with emerald glow
│   │   │   └── LoadingIndicator.tsx
│   │   └── hooks/
│   │       ├── useChat.ts       # Message state, send, retry, error handling
│   │       └── useSync.ts       # Sync trigger + status polling
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml           # Development (hot reload)
├── docker-compose.prod.yml      # Production (optimized)
├── .env.example
└── .gitignore
```
