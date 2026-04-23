from unittest.mock import MagicMock, patch

import pytest

from app.services.gemini import GeminiClient, GeminiError


@pytest.fixture
def fake_response():
    r = MagicMock()
    r.text = "hello world"
    r.usage_metadata = MagicMock(
        prompt_token_count=12,
        candidates_token_count=5,
    )
    return r


def test_generate_returns_text_and_token_counts(fake_response):
    with patch("app.services.gemini.genai") as genai:
        model = MagicMock()
        model.generate_content.return_value = fake_response
        genai.GenerativeModel.return_value = model

        client = GeminiClient(api_key="k", model_name="gemini-3.1-flash-lite")
        text, input_tokens, output_tokens = client.generate("prompt")

    assert text == "hello world"
    assert input_tokens == 12
    assert output_tokens == 5
    genai.configure.assert_called_once_with(api_key="k")
    genai.GenerativeModel.assert_called_once_with("gemini-3.1-flash-lite")
    model.generate_content.assert_called_once_with("prompt")


def test_generate_retries_on_transient_error(fake_response):
    with patch("app.services.gemini.genai") as genai, \
         patch("app.services.gemini.time.sleep") as sleep:
        model = MagicMock()
        model.generate_content.side_effect = [
            Exception("503 transient"),
            Exception("503 transient"),
            fake_response,
        ]
        genai.GenerativeModel.return_value = model

        client = GeminiClient(api_key="k", model_name="gemini-3.1-flash-lite")
        text, _, _ = client.generate("prompt")

    assert text == "hello world"
    assert model.generate_content.call_count == 3
    # exponential backoff: at least 2 sleeps between 3 attempts
    assert sleep.call_count == 2


def test_generate_raises_after_max_retries():
    with patch("app.services.gemini.genai") as genai, \
         patch("app.services.gemini.time.sleep"):
        model = MagicMock()
        model.generate_content.side_effect = Exception("503 transient")
        genai.GenerativeModel.return_value = model

        client = GeminiClient(api_key="k", model_name="gemini-3.1-flash-lite", max_retries=3)
        with pytest.raises(GeminiError):
            client.generate("prompt")

        assert model.generate_content.call_count == 3
