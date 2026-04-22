from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class Embedder:
    def __init__(self, model_name: str = MODEL_NAME):
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        vec = self._get_model().encode(text, show_progress_bar=False)
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vecs = self._get_model().encode(texts, show_progress_bar=False)
        return vecs.tolist()
