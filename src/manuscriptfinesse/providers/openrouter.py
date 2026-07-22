import json
import urllib.error
import urllib.request
from typing import Optional

from manuscriptfinesse.providers.base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "", model: str = "openrouter/auto", base_url: Optional[str] = None):
        self.api_key = api_key
        if model.startswith("openrouter/"):
            model = model.split("openrouter/", 1)[1]
        self.model = model
        self.base_url = base_url or "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouterProvider.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/manuscriptfinesse",
        }

        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                choices = resp_data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"OpenRouter API HTTP Error {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"OpenRouter API request failed: {e}") from e
