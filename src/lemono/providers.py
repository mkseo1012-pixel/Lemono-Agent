from __future__ import annotations

import os
import asyncio
import json
from abc import ABC, abstractmethod
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


def _post_json(url: str, payload: dict, headers: dict[str, str], timeout: float) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - provider URLs are fixed by operators
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise ProviderError(f"provider returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ProviderError(f"provider request failed: {type(exc).__name__}") from exc


class ModelProvider(ABC):
    name: str

    def __init__(self, timeout: float = 60):
        self.timeout = timeout

    @property
    @abstractmethod
    def configured(self) -> bool: ...

    @abstractmethod
    async def complete(self, model: str, system: str, message: str) -> str: ...


class OpenAICompatibleProvider(ModelProvider):
    def __init__(self, name: str, key_env: str, base_url: str, timeout: float = 60):
        super().__init__(timeout)
        self.name, self.key_env, self.base_url = name, key_env, base_url.rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(os.getenv(self.key_env))

    async def complete(self, model: str, system: str, message: str) -> str:
        key = os.getenv(self.key_env)
        if not key:
            raise ProviderError(f"{self.key_env} is not configured")
        payload = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": message}]}
        try:
            data = await asyncio.to_thread(
                _post_json,
                f"{self.base_url}/chat/completions",
                payload,
                {"Authorization": f"Bearer {key}"},
                self.timeout,
            )
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.name} returned an invalid response") from exc


class AnthropicProvider(ModelProvider):
    name = "claude"

    @property
    def configured(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    async def complete(self, model: str, system: str, message: str) -> str:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError("ANTHROPIC_API_KEY is not configured")
        payload = {"model": model, "max_tokens": 4096, "system": system, "messages": [{"role": "user", "content": message}]}
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
        try:
            data = await asyncio.to_thread(
                _post_json, "https://api.anthropic.com/v1/messages", payload, headers, self.timeout
            )
            return data["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("claude returned an invalid response") from exc


class GeminiProvider(ModelProvider):
    name = "gemini"

    @property
    def configured(self) -> bool:
        return bool(os.getenv("GEMINI_API_KEY"))

    async def complete(self, model: str, system: str, message: str) -> str:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise ProviderError("GEMINI_API_KEY is not configured")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?{urlencode({'key': key})}"
        payload = {"system_instruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": message}]}]}
        try:
            data = await asyncio.to_thread(_post_json, url, payload, {}, self.timeout)
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("gemini returned an invalid response") from exc


def build_providers(timeout: float = 60) -> dict[str, ModelProvider]:
    return {
        "openai": OpenAICompatibleProvider("openai", "OPENAI_API_KEY", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), timeout),
        "codex": OpenAICompatibleProvider("codex", "OPENAI_API_KEY", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), timeout),
        "grok": OpenAICompatibleProvider("grok", "XAI_API_KEY", os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"), timeout),
        "claude": AnthropicProvider(timeout),
        "gemini": GeminiProvider(timeout),
    }
