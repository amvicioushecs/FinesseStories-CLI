import os
from typing import Dict, Optional

from manuscriptfinesse.providers.base import BaseLLMProvider, MockProvider
from manuscriptfinesse.providers.gemini import GeminiProvider
from manuscriptfinesse.providers.openrouter import OpenRouterProvider


class LLMProviderFactory:
    @staticmethod
    def get_mock_provider(model: str = "mock-model", default_response: Optional[str] = None) -> BaseLLMProvider:
        return MockProvider(model=model, default_response=default_response)

    @classmethod
    def get_provider(cls, model_spec: str) -> BaseLLMProvider:
        if not model_spec or model_spec.startswith("mock"):
            return cls.get_mock_provider(model=model_spec or "mock-model")
        elif model_spec.startswith("gemini"):
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                return cls.get_mock_provider(model=model_spec)
            return GeminiProvider(api_key=api_key, model=model_spec)
        elif model_spec.startswith("openrouter"):
            api_key = os.getenv("OPENROUTER_API_KEY", "")
            if not api_key:
                return cls.get_mock_provider(model=model_spec)
            return OpenRouterProvider(api_key=api_key, model=model_spec)
        else:
            return cls.get_mock_provider(model=model_spec)

    @classmethod
    def get_provider_for_role(cls, role: str, role_map: Dict[str, str]) -> BaseLLMProvider:
        if role not in role_map:
            return cls.get_mock_provider(model=f"mock-{role}")
        model_spec = role_map[role]
        return cls.get_provider(model_spec)
