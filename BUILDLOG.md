# Build Log

## Pending End-to-End Tests (Gemini rate limit reset required)

Run these once the Gemini free tier quota resets (next day):

### 11.1 — Full RAG Flow
- [ ] `POST /chat` with `{"message": "hello"}` returns 200 with `response` and `sources`
- [ ] `POST /chat` with a real question returns relevant RAG-augmented answer from synced documents
- [ ] Response `sources` array includes `text_preview` field with chunk text
- [ ] Conversation history works: send a follow-up like "tell me more about that" and verify it uses context from the prior exchange

### 11.4 — Safety Limits (Live Verification)
- [ ] `GET /usage` shows `gemini_requests` and `gemini_tokens` incrementing after each chat call
- [ ] At 80% usage threshold, backend logs a warning (check `docker compose logs backend`)
- [ ] When daily limit is exceeded, `POST /chat` returns 429 with `{"error": "...", "limit_reached": true}`
- [ ] Frontend shows "Buddy is resting for today!" banner and disables input when 429 is received
- [ ] Retry button appears on non-limit errors (e.g., 502 from Gemini outage)

### 11.4 — Sync Limits
- [ ] `POST /sync` works and returns `files_processed`, `chunks_upserted`
- [ ] Incremental sync skips unchanged files (`files_skipped > 0` on second run)
- [ ] If vector limit would be exceeded, sync returns `limit_reached: true`

### Frontend Smoke Tests (browser)
- [ ] Dark/light mode toggle works — header and input bar switch correctly
- [ ] Suggestion buttons fill the text input (don't auto-send)
- [ ] Usage popover opens, shows bars, closes on click outside
- [ ] Source cards expand/collapse with text preview
- [ ] Error banner appears on failure with dismiss (X) and retry buttons
