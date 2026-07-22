import json
import urllib.error
import urllib.request
from typing import Optional

from manuscriptfinesse.providers.base import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "", model: str = "gemini-2.5-flash", base_url: Optional[str] = None):
        self.api_key = api_key
        if model.startswith("gemini/"):
            model = model.split("gemini/", 1)[1]
        self.model = model
        self.base_url = base_url or "https://generativelanguage.googleapis.com/v1beta/models"

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiProvider.")

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "generationConfig": {
                "temperature": temperature,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                candidates = resp_data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini API HTTP Error {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Gemini API request failed: {e}") from e
