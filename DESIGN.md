# Buddy - RAG Learning Project Design

**Date**: 2026-04-20
**Status**: Approved

## Overview

Buddy is a personal RAG (Retrieval-Augmented Generation) system that indexes documents from Google Drive and allows natural language queries against them. This is a learning project focused on:

- Building a complete RAG pipeline
- API key management and configuration
- Docker containerization
- Full-stack development (FastAPI + React)
- Test-driven development

## Architecture

```
                        Docker Compose
  ┌─────────────────────────┐    ┌─────────────────────────┐
  │   Frontend Container    │    │   Backend Container     │
  │   (React + Vite)        │───>│   (FastAPI + Python)    │
  │   Port 3000             │    │   Port 8000             │
  └─────────────────────────┘    └───────────┬─────────────┘
                                              │
                   ┌──────────────────────────┼──────────────────┐
                   │                          │                  │
                   v                          v                  v
           ┌──────────────┐          ┌──────────────┐    ┌─────────────┐
           │ Google Drive │          │   Pinecone   │    │   Gemini    │
           │     API      │          │  Vector DB   │    │     API     │
           └──────────────┘          └──────────────┘    └─────────────┘
```

### Technology Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Backend | FastAPI (Python) | REST API, async support |
| Frontend | React + Vite + Tailwind | Polished UI, not basic styling |
| Vector DB | Pinecone | Free tier: 1 index, 100K vectors |
| LLM | Google Gemini | Free tier: 15 RPM, 1M tokens/day |
| Embeddings | Sentence Transformers | Local, all-MiniLM-L6-v2 |
| OCR | Tesseract | Local, for scanned images |
| Containerization | Docker + docker-compose | Multi-container setup |

## Project Structure

```
buddy/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Pydantic Settings
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── chat.py      # POST /chat
│   │   │   │   ├── sync.py      # POST /sync, GET /sync/status
│   │   │   │   └── health.py    # GET /health
│   │   │   └── dependencies.py
│   │   └── services/
│   │       ├── drive.py         # Google Drive API wrapper
│   │       ├── document.py      # Document loading & chunking
│   │       ├── ocr.py           # Tesseract wrapper
│   │       ├── embeddings.py    # Sentence Transformers wrapper
│   │       ├── vectorstore.py   # Pinecone operations
│   │       └── rag.py           # RAG orchestration
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/
│   │   ├── integration/
│   │   └── mocks/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── SyncButton.tsx
│   │   │   └── StatusBadge.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts
│   │   │   └── useSync.ts
│   │   └── styles/
│   │       └── index.css
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── .env                          # Not committed
└── .gitignore
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check service connectivity |
| `/chat` | POST | Send query, get RAG-augmented response |
| `/sync` | POST | Trigger manual Google Drive sync |
| `/sync/status` | GET | Check sync status and last sync time |

### Request/Response Examples

**POST /chat**
```json
// Request
{ "message": "What did my professor say about recursion?" }

// Response
{
  "response": "Based on your CS201 notes, Professor Smith explained...",
  "sources": [
    { "file": "CS201-Lecture5.pdf", "page": 3 },
    { "file": "notes.docx", "chunk": 12 }
  ]
}
```

**GET /sync/status**
```json
{
  "is_running": false,
  "last_sync": "2026-04-20T10:30:00Z",
  "documents_indexed": 42
}
```

## Data Flow

### Sync Flow (Google Drive -> Pinecone)

```
Google Drive folder(s)
        │
        v
┌─────────────────┐
│   drive.py      │  List & download files
└────────┬────────┘
         │
         v
┌─────────────────┐
│  document.py    │  Parse PDFs, Docs
│     ocr.py      │  OCR for images
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Chunk text     │  500 tokens, 50 overlap
└────────┬────────┘
         │
         v
┌─────────────────┐
│ embeddings.py   │  Convert to vectors
└────────┬────────┘
         │
         v
┌─────────────────┐
│ vectorstore.py  │  Upsert to Pinecone
└─────────────────┘
```

### Query Flow (User Question -> Answer)

```
User: "What did my professor say about recursion?"
        │
        v
┌─────────────────┐
│ embeddings.py   │  Query -> vector
└────────┬────────┘
         │
         v
┌─────────────────┐
│ vectorstore.py  │  Search top 5 chunks
└────────┬────────┘
         │
         v
┌─────────────────┐
│    rag.py       │  Build prompt with context
└────────┬────────┘
         │
         v
┌─────────────────┐
│   Gemini API    │  Generate response
└────────┬────────┘
         │
         v
"Based on your CS201 notes..."
```

## Configuration & API Keys

### Environment Variables

**.env.example** (committed):
```bash
# Google Drive OAuth
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here

# Pinecone
PINECONE_API_KEY=your-pinecone-key
PINECONE_INDEX_NAME=buddy-index

# Google Gemini
GEMINI_API_KEY=your-gemini-key

# App settings
DRIVE_FOLDER_IDS=folder-id-1,folder-id-2
SYNC_ON_STARTUP=true
```

### Pydantic Settings (config.py)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    pinecone_api_key: str
    pinecone_index_name: str = "buddy-index"
    gemini_api_key: str
    drive_folder_ids: list[str]
    sync_on_startup: bool = True

    class Config:
        env_file = ".env"

settings = Settings()  # Validates on import
```

### API Key Sources

| Service | Where to Get |
|---------|--------------|
| Google Drive | console.cloud.google.com -> APIs & Services -> Credentials |
| Pinecone | pinecone.io -> API Keys |
| Gemini | aistudio.google.com -> Get API Key |

## Frontend Design

### Layout

```
┌─────────────────────────────────────────┐
│  [Status]           [Sync Now]  Last: 2m│  <- Header
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ You: What's in my CS201 notes? │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ Buddy: Based on your notes...  │    │  <- Chat history
│  │ - Topic 1: Recursion           │    │
│  │ - Topic 2: Big-O notation      │    │
│  └─────────────────────────────────┘    │
│                                         │
├─────────────────────────────────────────┤
│  [Type your question...      ] [Send]   │  <- Input
└─────────────────────────────────────────┘
```

### Styling

- Tailwind CSS (polished, not basic)
- Use `frontend` skill during implementation for high-quality UI

## Error Handling

| Scenario | Detection | User Experience |
|----------|-----------|-----------------|
| API key missing | Startup validation | App won't start + clear error |
| Drive auth expired | 401 response | "Please re-authenticate" prompt |
| Pinecone unreachable | Connection timeout | "Search unavailable, try again" |
| Gemini rate limited | 429 response | Auto-retry with backoff |
| OCR fails | Tesseract exception | Skip file, continue sync |
| Unsupported file type | Extension check | Skip file, continue sync |

## Structured Logging

### Log Schema

```json
{
  "timestamp": "2026-04-20T10:30:00Z",
  "level": "error | warn | info | debug",
  "category": "sync | chat | auth | system",
  "action": "what was being attempted",
  "context": { },
  "error": {
    "type": "ExceptionClassName",
    "message": "Human readable message",
    "recoverable": true
  }
}
```

### Categories

| Category | Actions |
|----------|---------|
| `sync` | `start`, `fetch_file`, `parse_document`, `ocr`, `embed`, `upsert`, `complete` |
| `chat` | `query_received`, `embed_query`, `retrieve`, `llm_call`, `response_sent` |
| `auth` | `oauth_start`, `oauth_callback`, `token_refresh`, `token_expired` |
| `system` | `startup`, `shutdown`, `health_check`, `config_loaded` |

### Implementation

Using Python's `structlog` library for structured JSON logging.

## Testing Strategy

### Test Structure

```
backend/tests/
├── conftest.py
├── unit/
│   ├── test_document.py
│   ├── test_embeddings.py
│   └── test_rag.py
├── integration/
│   ├── test_drive.py
│   ├── test_pinecone.py
│   └── test_chat_flow.py
└── mocks/
    └── fixtures/
```

### What Gets Mocked vs. Real

| Service | Unit Tests | Integration Tests |
|---------|------------|-------------------|
| Google Drive | Mock | Real (test folder) |
| Pinecone | Mock | Real (test index) |
| Gemini | Mock | Real |
| Tesseract | Mock | Real |
| Sentence Transformers | Mock | Real |

### TDD Approach

Use `tdd` skill during implementation:
1. Write failing test
2. Implement minimum code to pass
3. Refactor
4. Repeat

## Docker Configuration

### docker-compose.yml

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend:/app  # Dev: hot reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### Development Workflow

- `docker-compose up` - runs everything containerized
- `docker-compose up --build` - rebuild after dependency changes
- Can also run locally without Docker for faster iteration

## Implementation Notes

### Skills to Invoke

- `frontend` - for polished React/Tailwind UI work
- `tdd` - for test-driven development
- `executing_plans` - for following the implementation plan with checkpoints

### File Type Support

| Type | Handling |
|------|----------|
| Google Docs | Export as text via Drive API |
| PDF | PyPDF2 or pdfplumber |
| Images (PNG, JPG) | Tesseract OCR |
| Plain text / Markdown | Direct read |

### Chunking Parameters

- Chunk size: ~500 tokens
- Overlap: 50 tokens
- Metadata per chunk: `source_file`, `page`, `chunk_index`

### Sync Behavior

- Auto-sync on startup (configurable)
- Manual sync via button
- Tracks file hashes to avoid re-processing unchanged files
