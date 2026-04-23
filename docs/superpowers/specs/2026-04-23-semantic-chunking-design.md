# Semantic Chunking Migration Design

**Date**: 2026-04-23
**Status**: Approved
**Phase**: Post-deployment refactor (Phase 13)

## Overview

Replace Buddy's fixed-size token-window chunking (`chunk_text`) with LangChain's `SemanticChunker` for prose content and `RecursiveCharacterTextSplitter` for structured content (tables, code). This improves retrieval quality by aligning chunk boundaries with natural topic shifts rather than arbitrary token counts.

## Motivation

The current `chunk_text` function splits text into 500-token windows with 50-token overlap. This is simple and predictable but:

- Cuts mid-sentence, mid-paragraph, mid-section
- A concept spanning two paragraphs gets split across chunks
- No awareness of document structure (headings, lists, tables, code)
- One-size-fits-all regardless of content density

Buddy processes mixed content (lecture notes, spreadsheets, code, scanned images), so structure-aware chunking directly improves retrieval precision.

## Architecture

### New Files

```
backend/app/services/
├── langchain_embeddings.py    # Adapter: Embedder → LangChain Embeddings interface
├── text_preprocessor.py       # Content-aware block detection
```

### Modified Files

```
backend/app/services/
├── document.py                # New semantic_chunk(), remove chunk_text()
├── sync.py                    # Use semantic_chunk() with embedded vectors
├── config.py                  # Add chunking configuration
backend/
├── requirements.txt           # Add langchain packages, remove tiktoken
```

## Component Design

### 1. LangChain Embeddings Adapter

**File:** `backend/app/services/langchain_embeddings.py`

A thin wrapper around the existing `Embedder` class that implements LangChain's `Embeddings` interface. No state of its own — pass-through to the same singleton `Embedder` instance the rest of the app uses.

```
LangChainEmbeddingsAdapter
  - __init__(embedder: Embedder)
  - embed_documents(texts: list[str]) → list[list[float]]  # delegates to embedder.embed_batch()
  - embed_query(text: str) → list[float]                    # delegates to embedder.embed_text()
```

One model load, one model in memory. `SemanticChunker` uses the same `all-MiniLM-L6-v2` instance as the rest of the pipeline.

### 2. Content-Aware Pre-Processor

**File:** `backend/app/services/text_preprocessor.py`

Identifies and classifies blocks of text before they reach the chunker. Prevents LangChain's regex sentence splitter from mangling tables, code, and OCR noise.

```
ContentBlock:
  - text: str
  - block_type: "prose" | "table" | "code" | "ocr_raw"
  - skip_semantic: bool

preprocess_for_chunking(text: str, mime_type: str) → list[ContentBlock]
```

**Detection rules:**

| Block Type | Detection | skip_semantic |
|------------|-----------|---------------|
| Table | Lines with 2+ tab separators or pipe column patterns | True |
| Code | Text between triple backticks or consistently indented (4+ spaces) | True |
| OCR raw | When mime_type is `image/*` — light cleanup (collapse whitespace, strip stray chars) | False |
| Prose | Everything else | False |

### 3. Semantic Chunk Function

**File:** `backend/app/services/document.py`

Replaces `chunk_text`. Returns chunks with their embeddings already computed.

```
ChunkResult:
  - text: str
  - vector: list[float]
  - chunk_index: int

semantic_chunk(text: str, mime_type: str, embedder: Embedder) → list[ChunkResult]
```

**Flow:**

1. `preprocess_for_chunking(text, mime_type)` → list of `ContentBlock`
2. Prose blocks (`skip_semantic=False`):
   - `SemanticChunker(embeddings=adapter, breakpoint_threshold_type="percentile", breakpoint_threshold_amount=90.0)`
   - `create_documents([block.text])` → chunk texts
   - `embedder.embed_batch(chunk_texts)` → vectors for Pinecone
3. Structured blocks (`skip_semantic=True`):
   - Tables: `RecursiveCharacterTextSplitter(separators=["\n"], chunk_size=500, chunk_overlap=50)`
   - Code: `RecursiveCharacterTextSplitter(separators=["\n\n", "\n", " "], chunk_size=500, chunk_overlap=50)`
   - `embedder.embed_batch(chunk_texts)` → vectors
4. Return all `ChunkResult` objects in document order

**Embedding cost analysis:**

- SemanticChunker internally embeds sentences to decide split points (unavoidable overhead, uses same in-memory model)
- Final chunk embeddings are computed once and returned — replaces the separate `embed_batch` call in sync.py
- Net: one extra sentence-level embedding pass per document (the cost of semantic awareness), but no second model load or extra memory

### 4. Sync Pipeline Changes

**File:** `backend/app/services/sync.py`

Consolidate `chunk_text` + `embed_batch` into a single `semantic_chunk` call.

```
Before:
  chunks = chunk_text(text)
  vectors = self._embedder.embed_batch([c for c in chunks])

After:
  chunk_results = semantic_chunk(text, meta.mime_type, self._embedder)
```

Record building uses `ChunkResult.text` and `ChunkResult.vector` directly. No changes to dependency injection, change detection, state persistence, or vector limit checks.

### 5. Removed: `chunk_text`

The old `chunk_text` function is deleted entirely. All chunking goes through LangChain:
- Prose → `SemanticChunker`
- Tables/Code → `RecursiveCharacterTextSplitter`

## Dependencies

**Added to `requirements.txt`:**
- `langchain-experimental` — contains `SemanticChunker`
- `langchain-text-splitters` — contains `RecursiveCharacterTextSplitter`
- `langchain-core` — transitive dependency, provides `Embeddings` base class

**Removed from `requirements.txt`:**
- `tiktoken` — only used by `chunk_text` for `cl100k_base` encoding

## Configuration

**Added to `config.py`:**

```python
semantic_breakpoint_type: str = "percentile"
semantic_breakpoint_threshold: float = 90.0
structured_chunk_size: int = 500
structured_chunk_overlap: int = 50
```

- `percentile` at 90.0: split when embedding distance between consecutive sentences is in the top 10% of distances — more aggressive splitting for tighter topic-focused chunks, good for mixed content
- Structured settings mirror the old chunk_text defaults

## Testing

### New Test Files

**`test_semantic_chunking.py`:**
- Prose routes to SemanticChunker
- Tables route to RecursiveCharacterTextSplitter
- Code uses code-appropriate separators
- ChunkResults include vectors
- Document order preserved across mixed content

**`test_text_preprocessor.py`:**
- Detects markdown tables, pipe tables, tab-separated tables
- Detects code fences and indented code blocks
- OCR cleanup collapses whitespace
- Pure prose returns single block
- Mixed content returns ordered blocks

**`test_langchain_adapter.py`:**
- embed_documents delegates to embedder
- embed_query delegates to embedder
- Same model instance reused

### Updated Tests
- `test_document.py` — remove chunk_text tests, add semantic_chunk tests
- `test_sync.py` — expect ChunkResult objects instead of separate chunk + vector lists

### Integration Test
- `test_semantic_chunking_integration.py` — real mixed doc (prose + table + code) through semantic_chunk, verify coherent chunks with 384-dim vectors

## Migration Notes

- After deploying this change, a full re-sync is required to re-chunk all documents with the new strategy
- Existing Pinecone vectors from old chunking should be cleared and re-indexed (clear the index via Pinecone console, then trigger `POST /sync`)
- No API or frontend changes — the chat and sync endpoints remain identical
