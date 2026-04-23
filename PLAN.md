# Buddy - Implementation Plan

**Based on**: DESIGN.md
**Date**: 2026-04-20

This plan is organized into phases with checkpoints. Each phase builds on the previous one. Use the `tdd` skill for backend work and `frontend` skill for UI work.

---

## Phase 1: Project Scaffolding & Docker Setup

**Goal**: Get the basic project structure running in Docker with hot reload.

### Steps

1.1. **Create directory structure**
```
buddy/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── config.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── (Vite scaffolding)
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
└── .gitignore
```

1.2. **Backend Dockerfile**
- Python 3.11 slim base
- Install system dependencies (Tesseract)
- Install Python dependencies
- Hot reload with uvicorn --reload

1.3. **Frontend scaffolding**
- `npm create vite@latest` with React + TypeScript
- Add Tailwind CSS
- Create Dockerfile (Node base, Vite dev server)

1.4. **docker-compose.yml**
- Define backend and frontend services
- Volume mounts for hot reload
- Port mappings (8000, 3000)
- env_file configuration

1.5. **Create .env.example**
- All required environment variables with placeholder values
- Comments explaining each variable
- **Note**: Actual keys go in `.env` (gitignored), never in code

1.6. **Update .gitignore**
- Add .env, node_modules, __pycache__, .pytest_cache, etc.

### Checkpoint 1
- [ ] `docker-compose up` starts both containers
- [ ] Backend responds at http://localhost:8000
- [ ] Frontend loads at http://localhost:3000
- [ ] Changes to code trigger hot reload
- [ ] `.env` is in `.gitignore`

---

## Phase 2: Backend Configuration, Health Check & Usage Tracking

**Goal**: Pydantic settings working, health endpoint responding, usage tracking foundation.

### Steps

2.1. **config.py**
- Pydantic BaseSettings class
- All environment variables defined with types
- Validation on startup
- **Keys loaded from .env only** - never hardcoded

2.2. **Structured logging setup**
- Install and configure structlog
- JSON output format
- Category-based logging helper

2.3. **usage.py service (safety limits foundation)**
- Track API usage in local JSON file (`data/usage.json`, gitignored)
- Schema:
  ```json
  {
    "date": "2026-04-20",
    "gemini_requests": 0,
    "gemini_tokens": 0,
    "pinecone_vectors": 0
  }
  ```
- `check_limit(service, amount)` - returns True if safe to proceed
- `record_usage(service, amount)` - increment counters
- `get_usage_status()` - return current usage vs limits
- Auto-reset counters when date changes

2.4. **Safety limits configuration** (in config.py)
```python
# Conservative limits (below free tier max)
gemini_daily_requests: int = 1000      # Free tier: ~15 RPM
gemini_daily_tokens: int = 500000      # Free tier: 1M
pinecone_max_vectors: int = 80000      # Free tier: 100K
```

2.5. **Health endpoint**
- GET /health returns service status
- Include usage status (percentage of limits used)
- Check connectivity placeholders (will wire up later)

2.6. **Tests for config and usage**
- Test missing required vars raises error
- Test defaults work correctly
- Test usage tracking increments and resets

### Checkpoint 2
- [ ] App fails fast with clear error if required env vars missing
- [ ] GET /health returns JSON response with usage info
- [ ] Logs output in structured JSON format
- [ ] Usage tracking persists and resets daily

---

## Phase 3: API Keys Setup (User Action Required)

**Goal**: Get all API keys configured in .env file.

### Steps

3.1. **Google Cloud Project Setup**
- Create project in Google Cloud Console
- Enable Google Drive API
- Create OAuth 2.0 credentials (Desktop app)
- Download credentials, extract client_id and client_secret

3.2. **Pinecone Setup**
- Create free account at pinecone.io
- Create an index (name: buddy-index, dimension: 384 for MiniLM)
- Copy API key

3.3. **Gemini Setup**
- Go to aistudio.google.com
- Click "Get API Key"
- Copy API key

3.4. **Create .env file**
- Copy .env.example to .env
- Fill in all API keys
- Set DRIVE_FOLDER_IDS (get from Drive URL)
- **NEVER commit .env** - verify it's in .gitignore

### Checkpoint 3
- [ ] .env file exists with all keys filled in
- [ ] App starts without config errors
- [ ] `git status` does NOT show .env as tracked
- [ ] Keys are NOT visible anywhere in codebase

---

## Phase 4: Google Drive Service

**Goal**: Authenticate with Google Drive and list/download files.

### Steps

4.1. **OAuth flow implementation**
- Use google-auth-oauthlib
- Implement token storage (local file: `data/drive_token.json`, gitignored)
- Handle token refresh

4.2. **drive.py service**
- `authenticate()` - run OAuth flow if needed
- `list_files(folder_id)` - list files in a folder
- `download_file(file_id)` - download file content
- `get_file_metadata(file_id)` - get file info

4.3. **Handle Google Docs export**
- Export as plain text (not download)

4.4. **Tests**
- Unit tests with mocked responses
- Integration test with real test folder (manual)

### Checkpoint 4
- [ ] OAuth flow completes successfully
- [ ] Can list files in configured folder
- [ ] Can download PDF and export Google Doc
- [ ] Token persists between restarts
- [ ] Token file is gitignored

---

## Phase 5: Document Processing

**Goal**: Parse PDFs, Docs, and images into text chunks.

### Steps

5.1. **document.py service**
- `load_pdf(content)` - extract text from PDF bytes (pypdf)
- `load_docx(content)` - extract text from Word bytes (python-docx)
- `load_pptx(content)` - extract text from PowerPoint bytes (python-pptx)
- `load_xlsx(content)` - extract text from Excel bytes (openpyxl)
- `load_text(content)` - handle plain text (also for Google export
  output: text/plain and text/csv)
- `chunk_text(text)` - split into ~500 token chunks with overlap

5.2. **ocr.py service**
- `extract_text(image_bytes)` - Tesseract wrapper
- Handle common image formats (PNG, JPG)
- Return confidence score with text

5.3. **File type router**
- Detect file type from mime (with extension fallback)
- Route to appropriate loader:
  - `application/pdf` → load_pdf
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document` → load_docx
  - `application/vnd.openxmlformats-officedocument.presentationml.presentation` → load_pptx
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` → load_xlsx
  - `text/plain`, `text/csv`, `text/markdown` → load_text
  - `image/png`, `image/jpeg` → ocr.extract_text
- Skip unsupported types with warning

5.4. **Tests**
- Unit tests for chunking logic
- Test with sample PDF, docx, pptx, xlsx, image fixtures

### Checkpoint 5
- [ ] PDF text extraction works
- [ ] Office docs (.docx/.pptx/.xlsx) extract text
- [ ] Image OCR produces text
- [ ] Chunking produces correct sizes with overlap
- [ ] Unsupported files logged and skipped

---

## Phase 6: Embeddings & Vector Store (with Safety Limits)

**Goal**: Convert text to vectors and store in Pinecone, with usage limits.

### Steps

6.1. **embeddings.py service**
- Load sentence-transformers model (all-MiniLM-L6-v2)
- `embed_text(text)` - return vector
- `embed_batch(texts)` - batch embedding for efficiency

6.2. **vectorstore.py service**
- Initialize Pinecone client
- `upsert_chunks(chunks, metadata)` - store vectors
- `search(query_vector, top_k)` - retrieve similar chunks
- `delete_by_source(source_file)` - for re-syncing
- `get_vector_count()` - check current index size

6.3. **Pinecone safety limits**
- Before upsert, check: `current_vectors + new_vectors < 80K`
- If limit would be exceeded:
  - Log warning with category "system", action "limit_reached"
  - Return error: "Vector limit reached (80K). Delete old documents or wait for next month."
- Track vector count in usage.json

6.4. **Metadata schema**
- source_file, page/chunk_index, text preview

6.5. **Tests**
- Unit tests with mocked Pinecone
- Test limit checking logic
- Integration test upserting and querying

### Checkpoint 6
- [x] Embeddings generate 384-dim vectors
- [x] Chunks upsert to Pinecone successfully
- [x] Search returns relevant chunks
- [x] Upsert blocked if vector limit reached
- [x] Health endpoint shows Pinecone connected + vector count

---

## Phase 7: RAG Pipeline & Chat Endpoint (with Safety Limits)

**Goal**: Query flow working end-to-end, with Gemini usage limits.

### Steps

7.1. **rag.py service**
- `query(question)` - orchestrate full RAG flow:
  1. **Check Gemini daily limit first**
  2. Embed question
  3. Search Pinecone (top 5)
  4. Build prompt with context
  5. Call Gemini
  6. **Record token usage after call**
  7. Return response with sources

7.2. **Gemini safety limits**
- Before API call:
  - Check daily request count < 1000
  - Check daily token estimate < 500K
- If limit reached:
  - Log with category "chat", action "limit_reached"
  - Return friendly error: "Daily AI limit reached. Try again tomorrow!"
- After successful call:
  - Record actual token usage from response metadata
- At 80% usage: log warning

7.3. **Prompt template**
- System prompt defining assistant behavior
- Context injection format
- Source citation format

7.4. **Gemini integration**
- Use google-generativeai SDK (model: gemini-3.1-flash-lite)
- Handle rate limiting with exponential backoff retry
- Track tokens from response

7.5. **POST /chat endpoint**
- Accept { message: string }
- Return { response: string, sources: [...] }
- On limit reached: return { error: "...", limit_reached: true }

7.6. **GET /usage endpoint** (new)
- Return current usage stats and limits
- Percentage used for each service

7.7. **Tests**
- Unit test prompt building
- Unit test limit checking
- Integration test full flow

### Checkpoint 7
- [ ] POST /chat returns RAG-augmented response
- [ ] Sources are included in response
- [ ] Rate limiting handled with retry
- [ ] Daily limit blocks requests when exceeded
- [ ] GET /usage shows current stats
- [ ] Warning logged at 80% usage

---

## Phase 8: Sync Service & Endpoints

**Goal**: Sync Google Drive to Pinecone, manual and auto.

### Steps

8.1. **sync.py service**
- `run_sync()` - full sync flow:
  1. List files from configured folders
  2. Check hash/modified date vs last sync
  3. **Check Pinecone vector limit before processing**
  4. Download changed files
  5. Process and chunk
  6. Embed and upsert
  7. Update sync state
- Stop early if vector limit would be exceeded

8.2. **Sync state persistence**
- Track last sync time
- Track file hashes (detect changes)
- Store in local JSON file (`data/sync_state.json`)

8.3. **POST /sync endpoint**
- Trigger manual sync
- Return { started: true, job_id: string }
- If limit reached: { started: false, error: "Vector limit reached" }

8.4. **GET /sync/status endpoint**
- Return sync state, last sync time, doc count
- Include vector usage percentage

8.5. **Auto-sync on startup**
- If SYNC_ON_STARTUP=true, run sync when app starts
- Non-blocking (background task)
- Respect vector limits

8.6. **Tests**
- Unit test sync logic
- Test incremental sync (only changed files)
- Test limit enforcement

### Checkpoint 8
- [x] Manual sync processes all files
- [x] Incremental sync skips unchanged files
- [x] Sync stops gracefully at vector limit
- [x] Sync status endpoint works
- [x] Auto-sync triggers on startup

---

## Phase 8.5: Conversation Memory (Supermemory)

**Goal**: Add persistent conversation memory so Buddy remembers prior questions and builds user context across sessions.

### Design

Supermemory provides two capabilities we integrate:
1. **Memory storage** — after each chat turn, store the Q&A pair so Buddy can recall it later
2. **Memory retrieval** — before generating a response, fetch relevant past conversations and a user profile to inject into the Gemini prompt

The frontend sends recent conversation history with each request. The backend combines this short-term history with long-term Supermemory context and RAG document context to build a rich prompt.

### Steps

8.5.1. **Install supermemory Python SDK**
- Add `supermemory` to `requirements.txt`
- Add `SUPERMEMORY_API_KEY` to `.env.example` and `config.py`

8.5.2. **Create `memory.py` service** (`backend/app/services/memory.py`)
- Initialize `Supermemory` client with API key
- `store_conversation(user_msg, assistant_msg, container_tag)` — format and store a conversation turn via `client.add()`
- `get_memory_context(query, container_tag)` — call `client.profile()` to retrieve:
  - Static profile (long-term user facts)
  - Dynamic profile (recent patterns)
  - Relevant past conversation memories
- Return a formatted string ready for prompt injection
- Handle API failures gracefully (memory is enhancement, not critical path)

8.5.3. **Update `rag.py` — inject memory into prompt**
- Accept optional `history` (list of prior messages) and `memory_context` (from Supermemory)
- Update `PROMPT_TEMPLATE` to include:
  - Conversation memory section (from Supermemory)
  - Recent conversation history (from frontend)
  - RAG document context (existing)
- After generating response, call `memory.store_conversation()` asynchronously (fire-and-forget)

8.5.4. **Update `chat.py` endpoint**
- Extend `ChatRequest` to accept `history: list[dict]` (optional, recent messages from frontend)
- Before calling `rag.query()`:
  - Call `memory.get_memory_context(message)` to fetch Supermemory context
  - Pass both history and memory_context to the RAG service
- Keep the endpoint synchronous; memory storage is fire-and-forget

8.5.5. **Update `config.py`**
- Add `supermemory_api_key: str = ""` (optional — memory is an enhancement)
- Add `supermemory_container_tag: str = "buddy-default"`

8.5.6. **Update frontend `useChat.ts` hook**
- Send full conversation history with each chat request
- Trim history to last 10 messages to keep payload reasonable

8.5.7. **Update frontend `api/client.ts`**
- Update `ChatRequest` type: add `history` field
- Update `chat()` method to send history in POST body

8.5.8. **Update `.env.example`**
- Add `SUPERMEMORY_API_KEY` with placeholder and comment

### Checkpoint 8.5
- [ ] Supermemory SDK installed and configured
- [ ] `memory.py` can store and retrieve conversation memories
- [ ] RAG prompt includes memory context alongside document context
- [ ] Follow-up questions work ("what else?", "tell me more about that")
- [ ] Chat works normally if Supermemory API key is not set (graceful degradation)
- [ ] Frontend sends conversation history with each request
- [ ] Memory failures don't break the chat flow

---

## Phase 9: Frontend Foundation

**Goal**: React app with API client, full layout, sleek design with emerald glow.

**Note**: Invoke `frontend` skill for this phase. Complete rewrite of all frontend src/.

### Design System

**Theme: "Sleek Fetch"** — minimal, high-contrast, reactive glow.

**Color palette:**
- Dark mode: pure black `#000000` bg, `#34D399` emerald accent, white text
- Light mode: pure white `#FFFFFF` bg, `#047857` deep emerald accent, near-black text
- Borders: `#1a1a1a` (dark) / `#e5e5e5` (light)
- Muted text: `#737373` (dark) / `#525252` (light)

**NO glass/frosted/blur effects.** Clean solid surfaces only.

**Reactive emerald glow effects:**
- Buttons/cards on hover: `box-shadow: 0 0 15px rgba(16,185,129,0.3), 0 0 30px rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.5)`
- Send button: emerald pulse ripple on click
- Input focus: emerald ring glow
- Source cards: subtle emerald border glow on hover

**Typography:**
- Font: Geist Sans (Vercel) — load via `@fontsource/geist-sans` or CDN
- Single font family, weight 400/500/600/700

**Layout: centered conversation column**
- Narrow centered column (~max-w-3xl)
- Minimal header: "Buddy" name + paw icon, sync button, theme toggle, usage popover
- Chat messages in scrollable area
- Clean input bar at bottom (no glass, solid with glow on focus)

**Dog personality (minimal):**
- Paw-print icon as logo placeholder (user will add custom dog image later)
- No animated dog, no dog in empty state
- Fetch-themed copy: "Fetching your answer...", "Buddy found N sources"
- Paw-print avatar next to assistant messages

**Animations (spring physics, inspired by Roomie/DealyDigests):**
- Message entrance: fade + slide up (spring stiffness 260, damping 20)
- Source accordion: smooth height expand
- Loading: pulsing dots
- Buttons: scale on hover/tap (spring stiffness 400, damping 10)

**New frontend dependencies:**
- `motion` — React spring animations
- `lucide-react` — icon library
- `react-markdown` + `remark-gfm` — render Gemini markdown responses

### Steps

9.1. **Install dependencies & Geist font**
- `npm install motion lucide-react react-markdown remark-gfm`
- Load Geist Sans via CDN in index.html

9.2. **Design tokens & theme (index.css)**
- CSS variables for both modes (black/white bg, emerald accents)
- Dark/light mode via class toggle on `<html>` (respect system pref, manual override)
- Glow utility classes (`.glow-hover`, `.glow-focus`)
- No glass utilities

9.3. **API client (api/client.ts)**
- Fetch wrapper with base URL (`http://localhost:8000`)
- Methods: `chat(message)`, `triggerSync()`, `getSyncStatus()`, `getHealth()`, `getUsage()`
- Error handling: detect `limit_reached` in 429 responses, network errors
- TypeScript interfaces for all response shapes

9.4. **Theme manager (api/theme.ts)**
- `getInitialTheme()` — check localStorage then system preference
- `applyTheme(theme)` — toggle `dark` class on `<html>`

9.5. **Hooks (hooks/useChat.ts, hooks/useSync.ts)**
- useChat: message state, sendMessage, loading, error, limitReached, auto-scroll
- useSync: triggerSync, isSyncing, lastSync, filesCount

9.6. **Components (complete rewrite)**
- `Header.tsx` — minimal bar with name/paw, sync, theme toggle, usage popover
- `ChatMessage.tsx` — assistant (paw avatar, markdown, expandable sources with glow), user (right-aligned emerald)
- `ChatInput.tsx` — solid input with emerald glow on focus, send button with pulse
- `LoadingIndicator.tsx` — pulsing "Fetching..." with dots
- `App.tsx` — layout, empty state (just text + prompt hints, no dog illustration)

### Checkpoint 9
- [ ] Frontend connects to backend API
- [ ] Sleek black/white theme with emerald accents
- [ ] Dark/light mode toggle works
- [ ] Emerald glow on hover/focus interactions
- [ ] API client methods work
- [ ] Fetch-themed copy in empty state
- [ ] Limit errors handled gracefully

---

## Phase 10: Frontend Components

**Goal**: Complete chat interface with full dog/fetch personality.

**Note**: Invoke `frontend` skill for this phase.

### Steps

10.1. **useChat hook (hooks/useChat.ts)**
- Manage message history `{role, content, sources?}[]`
- `sendMessage(text)` → calls `client.chat()`, appends user + assistant messages
- Loading state (triggers "Fetching..." animation)
- Error state: detect `limit_reached`, network errors
- Auto-scroll to bottom on new message

10.2. **useSync hook (hooks/useSync.ts)**
- `triggerSync()` → calls `client.triggerSync()`
- Poll `client.getSyncStatus()` while syncing
- Expose: `isSyncing`, `lastSync`, `filesCount`, `syncResult`

10.3. **ChatMessage component**
- Assistant messages: Buddy dog avatar, emerald-tinted bubble, expandable source cards (glass effect)
- User messages: right-aligned, primary-colored bubble
- Message entrance animations via `motion`
- Source cards: file name, relevance score, expandable text preview
- Fetch-themed copy: "Buddy found N sources" as subtitle

10.4. **ChatInput component**
- Glass-effect floating bar at bottom
- Text input with send button (lucide Send icon)
- Enter to send, Shift+Enter for newline
- Disable + shimmer while waiting for response
- Show friendly message if daily limit reached ("Buddy is resting for today!")

10.5. **Header component**
- Buddy logo/name (left)
- SyncButton: paw-print icon, spinner while syncing, "Sync" label
- ThemeToggle: sun/moon icon, toggles dark/light
- UsagePopover: click to show usage bars (gemini requests, tokens, vectors)

10.6. **UsagePopover component**
- Emerald progress bars for each service
- Percentage labels
- Warning state (amber) at 80%+
- Danger state (red) at 95%+

### Checkpoint 10
- [ ] Can send message and see Buddy's response with avatar
- [ ] Sources displayed as expandable cards with glass effect
- [ ] Message entrance animations smooth
- [ ] Sync button works with loading state
- [ ] Theme toggle switches light/dark
- [ ] Usage popover shows stats with progress bars
- [ ] Limit reached shown to user gracefully ("Buddy is resting!")

---

## Phase 11: Integration Testing & Polish

**Goal**: Everything works together, edge cases handled.

### Steps

11.1. **End-to-end test flow**
- Start fresh (no data)
- Run sync
- Ask question
- Verify relevant response

11.2. **Error state UI**
- Handle API errors gracefully
- Show user-friendly messages for:
  - Network errors
  - Daily limit reached
  - Vector limit reached
  - Auth expired
- Retry options where appropriate

11.3. **Loading states**
- Skeleton loaders or spinners
- Disable inputs during operations

11.4. **Verify safety limits**
- Test that limits actually block requests
- Test usage resets at midnight
- Test warning logs at 80%

11.5. **Final polish**
- UI refinements
- Console warnings cleaned up
- Logging reviewed

### Checkpoint 11
- [ ] Full flow works end-to-end
- [ ] Error states handled gracefully
- [ ] Safety limits working correctly
- [ ] No console errors/warnings
- [ ] App feels polished

---

## Phase 12: Documentation & Deployment Prep

**Goal**: README complete, deployment-ready.

### Steps

12.1. **README.md**
- Project description
- Prerequisites
- Setup instructions (API keys)
- Running locally
- Running with Docker
- **Security note**: Never commit .env
- **Usage limits**: Explain the safety limits

12.2. **Verify .env.example is complete**

12.3. **Verify all sensitive files gitignored**
- .env
- data/drive_token.json
- data/usage.json
- data/sync_state.json

12.4. **Docker production builds**
- Multi-stage Dockerfiles
- Production docker-compose (no dev volumes)

12.5. **Final commit and push**

### Checkpoint 12
- [ ] README has complete setup instructions
- [ ] Security practices documented
- [ ] New developer could set up from README
- [ ] Production Docker builds work
- [ ] No secrets in git history

---

## Summary

| Phase | Description | Key Skill |
|-------|-------------|-----------|
| 1 | Project scaffolding & Docker | - |
| 2 | Backend config, health & usage tracking | tdd |
| 3 | API keys setup | (user action) |
| 4 | Google Drive service | tdd |
| 5 | Document processing | tdd |
| 6 | Embeddings & vector store + limits | tdd |
| 7 | RAG pipeline & chat + limits | tdd |
| 8 | Sync service | tdd |
| 8.5 | Conversation memory (Supermemory) | tdd |
| 9 | Frontend foundation | frontend |
| 10 | Frontend components | frontend |
| 11 | Integration & polish | - |
| 12 | Documentation | - |

## Safety Limits Summary

| Service | Free Tier | Our Limit | Tracked In |
|---------|-----------|-----------|------------|
| Gemini requests | ~15 RPM | 1000/day | usage.json |
| Gemini tokens | 1M/day | 500K/day | usage.json |
| Pinecone vectors | 100K | 80K | usage.json |

**Key safety features:**
- All API keys in `.env` only (gitignored)
- Usage tracked in local JSON file
- Limits checked before every API call
- Friendly error messages when limits hit
- Warnings logged at 80% usage
- Daily counters auto-reset
