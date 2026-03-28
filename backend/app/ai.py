import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

OPENROUTER_URL = "https://api.openrouter.ai/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b"
OPENROUTER_TIMEOUT_SECONDS = 15.0

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class OpenRouterError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def get_openrouter_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise OpenRouterError("OPENROUTER_API_KEY environment variable is required", status_code=500)
    return key


def run_openrouter_prompt(prompt: str, max_tokens: int = 32) -> dict[str, Any]:
    key = get_openrouter_api_key()

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(OPENROUTER_URL, json=payload, headers=headers, timeout=OPENROUTER_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise OpenRouterError("OpenRouter request failed") from exc
    except httpx.HTTPError as exc:
        raise OpenRouterError("OpenRouter request failed") from exc

    data = response.json()
    choices = data.get("choices")
    if not choices or not isinstance(choices, list) or not choices[0].get("message"):
        raise OpenRouterError("Unexpected OpenRouter response shape")

    text = choices[0]["message"].get("content")
    if not isinstance(text, str) or not text.strip():
        raise OpenRouterError("Unexpected OpenRouter response shape")

    return {
        "prompt": prompt,
        "response_text": text,
    }
