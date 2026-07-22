import io
import json
import os
from unittest.mock import MagicMock, patch
import pytest

from manuscriptfinesse.providers.base import BaseLLMProvider, MockProvider
from manuscriptfinesse.providers.gemini import GeminiProvider
from manuscriptfinesse.providers.openrouter import OpenRouterProvider
from manuscriptfinesse.providers.factory import LLMProviderFactory


def test_mock_provider():
    provider = MockProvider(model="test-mock", default_response="Mocked output")
    response = provider.generate(system_prompt="System prompt", user_prompt="User prompt")
    assert response == "Mocked output"

    provider_dynamic = MockProvider(model="test-mock")
    dyn_response = provider_dynamic.generate(system_prompt="Sys", user_prompt="Hello World")
    assert "Hello World" in dyn_response
    assert isinstance(provider_dynamic, BaseLLMProvider)


def test_gemini_provider_success():
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Gemini response text"}]
                }
            }
        ]
    }
    mock_response_bytes = json.dumps(mock_response_data).encode("utf-8")

    mock_http_response = MagicMock()
    mock_http_response.read.return_value = mock_response_bytes
    mock_http_response.__enter__.return_value = mock_http_response

    with patch("urllib.request.urlopen", return_value=mock_http_response) as mock_urlopen:
        provider = GeminiProvider(api_key="fake-gemini-key", model="gemini/gemini-2.5-flash")
        result = provider.generate(system_prompt="Be helpful", user_prompt="Write a story", temperature=0.5)

        assert result == "Gemini response text"
        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert "gemini-2.5-flash:generateContent?key=fake-gemini-key" in req.full_url
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["contents"][0]["parts"][0]["text"] == "Write a story"
        assert payload["systemInstruction"]["parts"][0]["text"] == "Be helpful"
        assert payload["generationConfig"]["temperature"] == 0.5


def test_gemini_provider_missing_key():
    provider = GeminiProvider(api_key="")
    with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
        provider.generate(system_prompt="Sys", user_prompt="User")


def test_openrouter_provider_success():
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": "OpenRouter response text"
                }
            }
        ]
    }
    mock_response_bytes = json.dumps(mock_response_data).encode("utf-8")

    mock_http_response = MagicMock()
    mock_http_response.read.return_value = mock_response_bytes
    mock_http_response.__enter__.return_value = mock_http_response

    with patch("urllib.request.urlopen", return_value=mock_http_response) as mock_urlopen:
        provider = OpenRouterProvider(api_key="fake-or-key", model="openrouter/free")
        result = provider.generate(system_prompt="System prompt", user_prompt="User prompt", temperature=0.8)

        assert result == "OpenRouter response text"
        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert req.headers["Authorization"] == "Bearer fake-or-key"
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["model"] == "free"
        assert payload["messages"][0] == {"role": "system", "content": "System prompt"}
        assert payload["messages"][1] == {"role": "user", "content": "User prompt"}


def test_openrouter_provider_missing_key():
    provider = OpenRouterProvider(api_key="")
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY is required"):
        provider.generate(system_prompt="Sys", user_prompt="User")


def test_llm_provider_factory_routing():
    role_map = {
        "miner": "gemini/gemini-2.5-flash",
        "drafter": "openrouter/free",
        "test_mock": "mock",
    }

    with patch.dict(os.environ, {"GEMINI_API_KEY": "env-gemini-key", "OPENROUTER_API_KEY": "env-or-key"}):
        miner_provider = LLMProviderFactory.get_provider_for_role("miner", role_map)
        assert isinstance(miner_provider, GeminiProvider)
        assert miner_provider.api_key == "env-gemini-key"
        assert miner_provider.model == "gemini-2.5-flash"

        drafter_provider = LLMProviderFactory.get_provider_for_role("drafter", role_map)
        assert isinstance(drafter_provider, OpenRouterProvider)
        assert drafter_provider.api_key == "env-or-key"
        assert drafter_provider.model == "free"

        mock_provider = LLMProviderFactory.get_provider_for_role("test_mock", role_map)
        assert isinstance(mock_provider, MockProvider)

        fallback_provider = LLMProviderFactory.get_provider_for_role("unmapped_role", role_map)
        assert isinstance(fallback_provider, MockProvider)

        explicit_mock = LLMProviderFactory.get_mock_provider()
        assert isinstance(explicit_mock, MockProvider)
