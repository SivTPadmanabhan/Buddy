"""Integration test for semantic chunking pipeline with real content."""

from unittest.mock import MagicMock, patch

from app.services.document import ChunkResult, semantic_chunk


def _make_real_embedder(dim=384):
    """Embedder that returns deterministic vectors based on text hash."""
    e = MagicMock()
    call_count = [0]

    def _embed_batch(texts):
        vecs = []
        for t in texts:
            call_count[0] += 1
            base = (hash(t) % 1000) / 1000.0
            vecs.append([base + (i * 0.001) for i in range(dim)])
        return vecs

    def _embed_text(text):
        base = (hash(text) % 1000) / 1000.0
        return [base + (i * 0.001) for i in range(dim)]

    e.embed_batch.side_effect = _embed_batch
    e.embed_text.side_effect = _embed_text
    return e


MIXED_DOCUMENT = """
Introduction to Data Structures

Data structures are fundamental to computer science. They provide organized ways
to store and access data efficiently. Understanding them is essential for writing
performant software. Different data structures offer different trade-offs between
insertion speed, lookup time, and memory usage.

Arrays are the simplest data structure. They store elements in contiguous memory
locations, providing O(1) random access. However, insertion and deletion at
arbitrary positions requires shifting elements, making these operations O(n).

| Structure | Lookup | Insert | Delete | Space |
| --- | --- | --- | --- | --- |
| Array | O(1) | O(n) | O(n) | O(n) |
| Linked List | O(n) | O(1) | O(1) | O(n) |
| Hash Table | O(1) | O(1) | O(1) | O(n) |
| Binary Tree | O(log n) | O(log n) | O(log n) | O(n) |

Here is a simple linked list implementation:

```python
class Node:
    def __init__(self, value):
        self.value = value
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def append(self, value):
        node = Node(value)
        if not self.head:
            self.head = node
            return
        current = self.head
        while current.next:
            current = current.next
        current.next = node
```

Linked lists are particularly useful when you need frequent insertions and
deletions at the beginning of the collection. They also form the basis for
more complex structures like stacks and queues.
""".strip()


def test_mixed_content_produces_coherent_chunks():
    embedder = _make_real_embedder()
    results = semantic_chunk(MIXED_DOCUMENT, "text/plain", embedder)

    assert len(results) >= 3
    assert all(isinstance(r, ChunkResult) for r in results)

    types_found = {"prose": False, "table": False, "code": False}
    for r in results:
        if "Structure" in r.text and "Lookup" in r.text and "|" in r.text:
            types_found["table"] = True
        elif "class Node" in r.text or "def __init__" in r.text:
            types_found["code"] = True
        elif "Data structures" in r.text or "Linked lists" in r.text:
            types_found["prose"] = True

    assert types_found["table"], "Should have a table chunk"
    assert types_found["code"], "Should have a code chunk"
    assert types_found["prose"], "Should have prose chunks"


def test_vectors_are_384_dimensional():
    embedder = _make_real_embedder()
    results = semantic_chunk(MIXED_DOCUMENT, "text/plain", embedder)

    for r in results:
        assert len(r.vector) == 384


def test_chunk_indices_are_sequential():
    embedder = _make_real_embedder()
    results = semantic_chunk(MIXED_DOCUMENT, "text/plain", embedder)

    indices = [r.chunk_index for r in results]
    assert indices == list(range(len(results)))


def test_no_empty_chunks_produced():
    embedder = _make_real_embedder()
    results = semantic_chunk(MIXED_DOCUMENT, "text/plain", embedder)

    for r in results:
        assert r.text.strip(), f"Empty chunk at index {r.chunk_index}"


def test_ocr_text_chunked_as_prose():
    embedder = _make_real_embedder()
    ocr_text = (
        "Chapter 1  Introduction\n"
        "This   document covers   the basics of   machine learning.\n"
        "Machine learning is a subset of artificial intelligence.\n"
        "It focuses on building systems that learn from data."
    )
    results = semantic_chunk(ocr_text, "image/png", embedder)

    assert len(results) >= 1
    assert all(isinstance(r, ChunkResult) for r in results)
    for r in results:
        assert "   " not in r.text


def test_pure_table_content():
    embedder = _make_real_embedder()
    table = "name\tscore\tgrade\nalice\t95\tA\nbob\t87\tB\ncharlie\t72\tC"
    results = semantic_chunk(table, "text/plain", embedder)

    assert len(results) >= 1
    assert "alice" in results[0].text


def test_pure_code_content():
    embedder = _make_real_embedder()
    code = "```python\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n```"
    results = semantic_chunk(code, "text/plain", embedder)

    assert len(results) >= 1
    assert "factorial" in results[0].text
