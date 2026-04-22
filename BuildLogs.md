# Buddy — Build Logs

## 2026-04-22: Conversation Memory (Supermemory Integration)

### Problem

Buddy treats every chat message as independent — no awareness of prior questions or answers. If a user asks "What is a linked list?" and then follows up with "Can you give me an example?", Buddy has no idea what "that" refers to. The Gemini model receives only the current question + RAG document context, with zero conversation history.

### Solution: Supermemory API

Integrate [Supermemory](https://supermemory.ai) to provide two layers of memory:

1. **Short-term**: Frontend sends the recent conversation history (last 10 messages) with each request, giving Gemini immediate conversational context.
2. **Long-term**: Supermemory stores every conversation turn and builds a semantic memory graph. Before each response, we query Supermemory for relevant past conversations and a user profile, injecting this into the prompt.

### Architecture Change

```
BEFORE:
  User message → Embed → Pinecone search → Build prompt (RAG only) → Gemini → Response

AFTER:
  User message → Embed → Pinecone search ─────────────────┐
                       → Supermemory.profile() ────────────┤
                       → Frontend history (last 10 msgs) ──┤
                                                           v
                                              Build prompt (RAG + memory + history) → Gemini → Response
                                                                                        │
                                                                                        v
                                                                          Supermemory.add() (async, fire-and-forget)
```

### Files Changed

#### Backend

| File | Change | Details |
|------|--------|---------|
| `backend/requirements.txt` | Add dependency | Add `supermemory` package |
| `backend/app/config.py` | Add config fields | `supermemory_api_key: str = ""` (optional), `supermemory_container_tag: str = "buddy-default"` |
| `backend/app/services/memory.py` | **New file** | Supermemory client wrapper with `store_conversation()` and `get_memory_context()` |
| `backend/app/services/rag.py` | Modify `query()` | Accept `history` and `memory_context` params; update prompt template to include memory sections; fire-and-forget memory storage after response |
| `backend/app/api/chat.py` | Modify endpoint | Extend `ChatRequest` with optional `history` field; call memory service before RAG; pass context through |
| `.env.example` | Add variable | `SUPERMEMORY_API_KEY=your-supermemory-api-key` |

#### Frontend

| File | Change | Details |
|------|--------|---------|
| `frontend/src/api/client.ts` | Update types & method | Add `history` to chat request body |
| `frontend/src/hooks/useChat.ts` | Send history | Pass last 10 messages with each `chat()` call |

### Detailed Change Specifications

---

#### 1. `backend/requirements.txt`

Add at the end:
```
supermemory
```

---

#### 2. `backend/app/config.py`

Add two fields to `Settings`:
```python
supermemory_api_key: str = ""
supermemory_container_tag: str = "buddy-default"
```

Empty string default means memory is opt-in. If not configured, the memory service returns empty context and skips storage.

---

#### 3. `backend/app/services/memory.py` (new file)

```python
from supermemory import Supermemory
from app.logging_config import get_logger

log = get_logger(__name__)


class MemoryService:
    def __init__(self, api_key: str, container_tag: str = "buddy-default"):
        self._enabled = bool(api_key)
        self._container_tag = container_tag
        if self._enabled:
            self._client = Supermemory(api_key=api_key)

    def get_memory_context(self, query: str) -> str:
        """Fetch user profile + relevant memories. Returns formatted string for prompt injection."""
        if not self._enabled:
            return ""
        try:
            profile = self._client.profile(
                container_tag=self._container_tag,
                q=query,
            )
            parts = []
            if profile.profile.static:
                parts.append("User facts:\n" + "\n".join(profile.profile.static))
            if profile.profile.dynamic:
                parts.append("Recent patterns:\n" + "\n".join(profile.profile.dynamic))
            if profile.search_results and profile.search_results.results:
                memories = "\n".join(
                    r.get("memory", "") for r in profile.search_results.results if r.get("memory")
                )
                if memories:
                    parts.append("Relevant past conversations:\n" + memories)
            return "\n\n".join(parts)
        except Exception as e:
            log.warning("memory_fetch_failed", category="memory", action="get_context", error=str(e))
            return ""

    def store_conversation(self, user_msg: str, assistant_msg: str) -> None:
        """Store a conversation turn. Fire-and-forget — failures are logged, not raised."""
        if not self._enabled:
            return
        try:
            self._client.add(
                content=f"user: {user_msg}\nassistant: {assistant_msg}",
                container_tag=self._container_tag,
            )
        except Exception as e:
            log.warning("memory_store_failed", category="memory", action="store", error=str(e))
```

Key design decisions:
- **Graceful degradation**: If `api_key` is empty, all methods return early. Memory is never a hard dependency.
- **Error isolation**: All Supermemory calls are wrapped in try/except. A Supermemory outage doesn't break chat.
- **Formatted output**: `get_memory_context()` returns a pre-formatted string ready for prompt injection, keeping RAG service clean.

---

#### 4. `backend/app/services/rag.py`

**Prompt template update** — add memory and history sections:

```python
PROMPT_TEMPLATE = """...(existing instructions)...

{memory_section}

{history_section}

User Query: {query}
<context>
{context}
</context>
"""
```

Where:
- `memory_section` = Supermemory context (long-term memory), wrapped in `<memory>` tags if non-empty
- `history_section` = Recent conversation history from frontend, formatted as `User: ...\nAssistant: ...`

**`query()` method changes**:
- Add parameters: `history: list[dict] | None = None`, `memory_context: str = ""`
- Build `history_section` from the history list
- Build `memory_section` from the memory_context string
- After getting Gemini response, call `memory.store_conversation()` (fire-and-forget via threading)
- Accept a `memory_service` reference (injected from chat endpoint)

---

#### 5. `backend/app/api/chat.py`

**Request model change**:
```python
class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None  # [{"role": "user"|"assistant", "content": "..."}]
```

**Endpoint logic change**:
- Instantiate `MemoryService` (via `_build_memory_service()`, cached like RAG service)
- Call `memory.get_memory_context(req.message)` before RAG query
- Pass `history=req.history` and `memory_context=memory_context` to `rag.query()`

---

#### 6. `.env.example`

Add:
```bash
# Supermemory (conversation memory — optional, chat works without it)
# Get this from: console.supermemory.ai -> API Keys
SUPERMEMORY_API_KEY=your-supermemory-api-key
```

---

#### 7. `frontend/src/api/client.ts`

Update the `chat()` method to accept and send history:
```typescript
chat: (message: string, history?: { role: string; content: string }[]) =>
  request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, history }),
  }),
```

---

#### 8. `frontend/src/hooks/useChat.ts`

In `sendMessage()`, pass the last 10 messages as history:
```typescript
const recent = messages.slice(-10).map(m => ({ role: m.role, content: m.content }));
const res = await api.chat(trimmed, recent);
```

This sends the current in-session conversation to the backend. Combined with Supermemory's long-term memory, Buddy gets both immediate conversational context and cross-session recall.

### Testing Plan

1. **Unit test `memory.py`** — mock Supermemory client, verify store/retrieve formatting
2. **Unit test `rag.py`** — verify prompt includes memory sections when provided, omits when empty
3. **Integration test** — send two related messages, verify second response references the first
4. **Graceful degradation test** — unset `SUPERMEMORY_API_KEY`, verify chat still works normally

### Rollback

If Supermemory causes issues:
- Set `SUPERMEMORY_API_KEY=""` in `.env` → memory service disables itself
- No code changes needed, chat falls back to stateless RAG-only mode

---

## 2026-04-22: Bug Fixes (Pre-Memory)

Three bugs fixed that were preventing the app from working:

### Bug 1: numpy 2.x / PyTorch ABI incompatibility

- **Symptom**: POST /chat returns 500, `RuntimeError: Numpy is not available`
- **Root cause**: `torch==2.2.2` compiled against numpy 1.x, but pip resolved `numpy==2.4.4`
- **Fix**: Pinned `numpy<2` in `requirements.txt`
- **File**: `backend/requirements.txt`

### Bug 2: numpy.float32 not serializable by Pinecone

- **Symptom**: POST /chat returns 500, `AttributeError: 'numpy.float32' object has no attribute '_composed_schemas'`
- **Root cause**: `list(numpy_array)` produces `numpy.float32` elements; Pinecone's serializer can't handle them
- **Fix**: Changed `list(vec)` → `vec.tolist()` in `embed_text()` and `embed_batch()`
- **File**: `backend/app/services/embeddings.py`

### Bug 3: Pinecone "Namespace not found" on first sync

- **Symptom**: Every file fails during sync with 404 "Namespace not found"
- **Root cause**: `delete_by_source()` calls `index.delete(filter=...)` which fails on an empty index where the default namespace doesn't exist yet
- **Fix**: Catch the "Namespace not found" exception and return silently (nothing to delete is not an error)
- **File**: `backend/app/services/vectorstore.py`
