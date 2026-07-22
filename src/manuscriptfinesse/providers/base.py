from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """Submits prompts to the underlying LLM provider and returns string completion."""
        pass


class MockProvider(BaseLLMProvider):
    def __init__(self, model: str = "mock-model", default_response: Optional[str] = None):
        self.model = model
        self.default_response = default_response

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        if self.default_response is not None:
            return self.default_response
        return f"[MOCK GENERATION ({self.model}): system='{system_prompt[:30]}...', user='{user_prompt[:50]}...']"
