import os
from typing import Dict, Optional, Any
import yaml
from pydantic import BaseModel, Field

class ProviderConfig(BaseModel):
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None

class ProjectConfig(BaseModel):
    providers: Dict[str, ProviderConfig] = Field(default_factory=lambda: {
        "gemini": ProviderConfig(api_key_env="GEMINI_API_KEY"),
        "openrouter": ProviderConfig(api_key_env="OPENROUTER_API_KEY"),
        "openai": ProviderConfig(api_key_env="OPENAI_API_KEY"),
        "anthropic": ProviderConfig(api_key_env="ANTHROPIC_API_KEY"),
        "ollama": ProviderConfig(base_url="http://localhost:11434"),
    })
    role_routing: Dict[str, str] = Field(default_factory=lambda: {
        "miner": "gemini/gemini-2.5-flash",
        "dossier_builder": "gemini/gemini-2.5-pro",
        "synthesizer": "gemini/gemini-2.5-flash",
        "outliner": "gemini/gemini-2.5-flash",
        "drafter": "anthropic/claude-3-5-sonnet",
        "auditor": "gemini/gemini-2.5-pro",
        "polisher": "openai/gpt-4o",
    })

    @classmethod
    def load(cls, filepath: str) -> "ProjectConfig":
        if not os.path.exists(filepath):
            return cls()
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    def save(self, filepath: str) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.model_dump(), f)
