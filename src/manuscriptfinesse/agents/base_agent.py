from abc import ABC, abstractmethod
import os
from typing import Optional
from manuscriptfinesse.providers.base import BaseLLMProvider


def load_input(raw_input: str) -> str:
    """Helper function to load content from a file path if it exists, or return raw text string."""
    if isinstance(raw_input, str) and "\n" not in raw_input and "\r" not in raw_input:
        try:
            if os.path.exists(raw_input) and os.path.isfile(raw_input):
                with open(raw_input, "r", encoding="utf-8") as f:
                    return f.read()
        except (OSError, ValueError):
            pass
    return raw_input


class BaseAgent(ABC):
    """Abstract base class for all ManuscriptFinesse processing agents."""

    def __init__(self, provider: BaseLLMProvider, system_prompt: Optional[str] = None):
        self.provider = provider
        self.system_prompt = system_prompt or "You are an AI assistant for ManuscriptFinesse."

    @abstractmethod
    def run(self, raw_input: str) -> str:
        """Executes the agent task against raw_input (text or file path) and returns generated output."""
        pass
