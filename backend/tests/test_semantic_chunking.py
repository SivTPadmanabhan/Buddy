from unittest.mock import MagicMock, patch

import pytest

from app.services.document import ChunkResult, semantic_chunk
from app.services.text_preprocessor import ContentBlock


def _make_embedder(dim=384):
    e = MagicMock()
    call_count = [0]

    def _embed_batch(texts):
        vecs = []
        for _ in texts:
            call_count[0] += 1
            vecs.append([float(call_count[0])] * dim)
        return vecs

    e.embed_batch.side_effect = _embed_batch
    e.embed_text.return_value = [0.5] * dim
    return e


def test_prose_uses_semantic_chunker():
    embedder = _make_embedder()
    text = "This is about recursion. " * 50 + "\n\nThis is about sorting. " * 50

    with patch("app.services.document.SemanticChunker") as MockChunker:
        mock_instance = MockChunker.return_value
        mock_instance.create_documents.return_value = [
            MagicMock(page_content="This is about recursion. " * 50),
            MagicMock(page_content="This is about sorting. " * 50),
        ]

        results = semantic_chunk(text, "text/plain", embedder)

    assert MockChunker.called
    assert len(results) == 2
    assert all(isinstance(r, ChunkResult) for r in results)


def test_table_uses_recursive_splitter():
    embedder = _make_embedder()
    text = "| Name | Score |\n| --- | --- |\n| Alice | 10 |\n| Bob | 20 |"

    with patch("app.services.document.RecursiveCharacterTextSplitter") as MockSplitter:
        mock_instance = MockSplitter.return_value
        mock_instance.split_text.return_value = [text]

        results = semantic_chunk(text, "text/plain", embedder)

    assert MockSplitter.called
    init_kwargs = MockSplitter.call_args[1]
    assert "\n" in init_kwargs["separators"]


def test_code_uses_recursive_splitter_with_code_separators():
    embedder = _make_embedder()
    text = "```python\ndef hello():\n    print('hi')\n```"

    with patch("app.services.document.RecursiveCharacterTextSplitter") as MockSplitter:
        mock_instance = MockSplitter.return_value
        mock_instance.split_text.return_value = [text]

        results = semantic_chunk(text, "text/plain", embedder)

    assert MockSplitter.called
    init_kwargs = MockSplitter.call_args[1]
    assert "\n\n" in init_kwargs["separators"]


def test_chunk_results_include_vectors():
    embedder = _make_embedder()
    text = "A short paragraph about testing."

    with patch("app.services.document.SemanticChunker") as MockChunker:
        mock_instance = MockChunker.return_value
        mock_instance.create_documents.return_value = [
            MagicMock(page_content="A short paragraph about testing."),
        ]

        results = semantic_chunk(text, "text/plain", embedder)

    assert len(results) == 1
    assert len(results[0].vector) == 384
    assert results[0].text == "A short paragraph about testing."
    embedder.embed_batch.assert_called()


def test_document_order_preserved():
    embedder = _make_embedder()
    text = (
        "Introduction to algorithms.\n\n"
        "| Type | Speed |\n| --- | --- |\n| Quick | O(nlogn) |\n\n"
        "Conclusion about performance."
    )

    with patch("app.services.document.SemanticChunker") as MockChunker, \
         patch("app.services.document.RecursiveCharacterTextSplitter") as MockSplitter:

        mock_chunker = MockChunker.return_value
        mock_chunker.create_documents.side_effect = [
            [MagicMock(page_content="Introduction to algorithms.")],
            [MagicMock(page_content="Conclusion about performance.")],
        ]
        mock_splitter = MockSplitter.return_value
        mock_splitter.split_text.return_value = [
            "| Type | Speed |\n| --- | --- |\n| Quick | O(nlogn) |"
        ]

        results = semantic_chunk(text, "text/plain", embedder)

    assert results[0].text == "Introduction to algorithms."
    assert "Type" in results[1].text
    assert results[2].text == "Conclusion about performance."


def test_chunk_index_assigned_sequentially():
    embedder = _make_embedder()
    text = "First topic. " * 30 + "\n\nSecond topic. " * 30

    with patch("app.services.document.SemanticChunker") as MockChunker:
        mock_instance = MockChunker.return_value
        mock_instance.create_documents.return_value = [
            MagicMock(page_content="First topic. " * 30),
            MagicMock(page_content="Second topic. " * 30),
        ]

        results = semantic_chunk(text, "text/plain", embedder)

    indices = [r.chunk_index for r in results]
    assert indices == list(range(len(results)))


def test_empty_text_returns_empty():
    embedder = _make_embedder()
    results = semantic_chunk("", "text/plain", embedder)
    assert results == []


def test_whitespace_only_returns_empty():
    embedder = _make_embedder()
    results = semantic_chunk("   \n\n  ", "text/plain", embedder)
    assert results == []
