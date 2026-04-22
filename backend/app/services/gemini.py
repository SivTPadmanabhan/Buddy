import time

import google.generativeai as genai

from app.logging_config import get_logger


log = get_logger(__name__)


class GeminiError(Exception):
    pass


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        max_retries: int = 3,
        initial_backoff: float = 1.0,
    ):
        self._model_name = model_name
        self._max_retries = max_retries
        self._initial_backoff = initial_backoff
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str) -> tuple[str, int, int]:
        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._model.generate_content(prompt)
                usage = getattr(response, "usage_metadata", None)
                input_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
                output_tokens = int(getattr(usage, "candidates_token_count", 0) or 0)
                return response.text, input_tokens, output_tokens
            except Exception as e:
                last_error = e
                log.warning(
                    "gemini_generate_failed",
                    category="gemini",
                    action="retry",
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < self._max_retries - 1:
                    time.sleep(self._initial_backoff * (2 ** attempt))
        raise GeminiError(
            f"Gemini generate failed after {self._max_retries} attempts: {last_error}"
        )
