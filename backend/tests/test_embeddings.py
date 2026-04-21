from unittest.mock import MagicMock, patch

import pytest


def test_embed_text_returns_vector():
    from app.services.embeddings import Embedder

    fake_model = MagicMock()
    fake_model.encode.return_value = [0.1] * 384

    with patch("app.services.embeddings.SentenceTransformer", return_value=fake_model):
        emb = Embedder()
        vec = emb.embed_text("hello world")

    assert isinstance(vec, list)
    assert len(vec) == 384
    fake_model.encode.assert_called_once_with("hello world", show_progress_bar=False)


def test_embed_batch_returns_list_of_vectors():
    from app.services.embeddings import Embedder

    fake_model = MagicMock()
    fake_model.encode.return_value = [[0.1] * 384, [0.2] * 384, [0.3] * 384]

    with patch("app.services.embeddings.SentenceTransformer", return_value=fake_model):
        emb = Embedder()
        vecs = emb.embed_batch(["a", "b", "c"])

    assert len(vecs) == 3
    assert all(len(v) == 384 for v in vecs)
    fake_model.encode.assert_called_once()


def test_embedder_lazy_loads_model():
    from app.services.embeddings import Embedder

    with patch("app.services.embeddings.SentenceTransformer") as mock_cls:
        emb = Embedder()
        mock_cls.assert_not_called()
        emb.embed_text("x")
        mock_cls.assert_called_once_with("sentence-transformers/all-MiniLM-L6-v2")


def test_embed_batch_empty_returns_empty():
    from app.services.embeddings import Embedder

    with patch("app.services.embeddings.SentenceTransformer") as mock_cls:
        emb = Embedder()
        assert emb.embed_batch([]) == []
        mock_cls.assert_not_called()
