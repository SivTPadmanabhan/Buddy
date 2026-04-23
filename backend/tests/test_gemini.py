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
    with patch("app.services.gemini.genai") as mock_genai:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = fake_response
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="k", model_name="gemini-3.1-flash-lite-preview")
        text, input_tokens, output_tokens = client.generate("prompt")

    assert text == "hello world"
    assert input_tokens == 12
    assert output_tokens == 5
    mock_genai.Client.assert_called_once_with(api_key="k")
    mock_client.models.generate_content.assert_called_once_with(
        model="gemini-3.1-flash-lite-preview",
        contents="prompt",
    )


def test_generate_retries_on_transient_error(fake_response):
    with patch("app.services.gemini.genai") as mock_genai, \
         patch("app.services.gemini.time.sleep") as sleep:
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [
            Exception("503 transient"),
            Exception("503 transient"),
            fake_response,
        ]
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="k", model_name="gemini-3.1-flash-lite-preview")
        text, _, _ = client.generate("prompt")

    assert text == "hello world"
    assert mock_client.models.generate_content.call_count == 3
    assert sleep.call_count == 2


def test_generate_raises_after_max_retries():
    with patch("app.services.gemini.genai") as mock_genai, \
         patch("app.services.gemini.time.sleep"):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("503 transient")
        mock_genai.Client.return_value = mock_client

        client = GeminiClient(api_key="k", model_name="gemini-3.1-flash-lite-preview", max_retries=3)
        with pytest.raises(GeminiError):
            client.generate("prompt")

        assert mock_client.models.generate_content.call_count == 3
