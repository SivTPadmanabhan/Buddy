from unittest.mock import MagicMock

from app.services.langchain_embeddings import LangChainEmbeddingsAdapter


def _make_embedder():
    e = MagicMock()
    e.embed_text.return_value = [0.1] * 384
    e.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]
    return e


def test_embed_documents_delegates_to_embed_batch():
    embedder = _make_embedder()
    adapter = LangChainEmbeddingsAdapter(embedder)

    result = adapter.embed_documents(["hello", "world"])

    embedder.embed_batch.assert_called_once_with(["hello", "world"])
    assert result == [[0.1] * 384, [0.2] * 384]


def test_embed_query_delegates_to_embed_text():
    embedder = _make_embedder()
    adapter = LangChainEmbeddingsAdapter(embedder)

    result = adapter.embed_query("hello")

    embedder.embed_text.assert_called_once_with("hello")
    assert result == [0.1] * 384


def test_same_embedder_instance_reused():
    embedder = _make_embedder()
    adapter = LangChainEmbeddingsAdapter(embedder)

    adapter.embed_documents(["a"])
    adapter.embed_query("b")
    adapter.embed_documents(["c"])

    assert embedder.embed_batch.call_count == 2
    assert embedder.embed_text.call_count == 1
