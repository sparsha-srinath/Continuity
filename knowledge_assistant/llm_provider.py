from __future__ import annotations

import json
import math
import os
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


class ProviderError(RuntimeError):
    """A configured model provider could not return a usable response."""


@dataclass(frozen=True)
class ProviderConfig:
    provider: str = "none"
    model: str = ""
    api_key: str = ""
    base_url: str = ""
    timeout_seconds: float = 30.0
    context_tokens: int = 8192
    max_output_tokens: int = 600
    local_api: str = "auto"

    @property
    def uses_ollama(self) -> bool:
        endpoint = urlsplit(self.base_url)
        return self.provider == "local" and (
            self.local_api == "ollama"
            or (self.local_api == "auto" and endpoint.hostname in {"localhost", "127.0.0.1", "::1"}
                and endpoint.port == 11434)
        )


def _local_secrets() -> dict[str, Any]:
    secrets_path = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return {}
    try:
        with secrets_path.open("rb") as secrets_file:
            return tomllib.load(secrets_file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ProviderError(f"Unable to read .streamlit/secrets.toml: {error}") from error


def load_provider_config(
    environ: dict[str, str] | None = None,
    secrets: dict[str, Any] | None = None,
) -> ProviderConfig:
    environment = os.environ if environ is None else environ
    secret_values = _local_secrets() if secrets is None else secrets

    def setting(name: str, default: str = "") -> str:
        environment_value = str(environment.get(name, "")).strip()
        secret_value = str(secret_values.get(name, "")).strip()
        return environment_value or secret_value or default

    provider = setting("LLM_PROVIDER", "none").lower()
    if provider not in {"none", "openai", "anthropic", "local"}:
        raise ProviderError("LLM_PROVIDER must be one of: none, openai, anthropic, local")

    defaults = {
        "openai": ("gpt-4o-mini", "https://api.openai.com/v1"),
        "anthropic": ("claude-3-5-haiku-latest", "https://api.anthropic.com/v1"),
        "local": ("qwen2.5:7b", "http://localhost:11434/v1"),
    }
    model_default, url_default = defaults.get(provider, ("", ""))
    api_key_name = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "local": "LOCAL_LLM_API_KEY"}.get(provider, "")
    api_key = setting(api_key_name) if api_key_name else ""
    if provider in {"openai", "anthropic"} and not api_key:
        raise ProviderError(f"{api_key_name} is required when LLM_PROVIDER={provider}")

    timeout_text = setting("LLM_TIMEOUT_SECONDS", "30")
    try:
        timeout_seconds = float(timeout_text)
    except ValueError as error:
        raise ProviderError("LLM_TIMEOUT_SECONDS must be a number") from error
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ProviderError("LLM_TIMEOUT_SECONDS must be greater than zero")

    try:
        context_tokens = int(setting("LLM_CONTEXT_TOKENS", "8192"))
        max_output_tokens = int(setting("LLM_MAX_OUTPUT_TOKENS", "600"))
    except ValueError as error:
        raise ProviderError("Context and output token limits must be integers") from error
    if context_tokens < 2048 or not 128 <= max_output_tokens <= context_tokens - 1024:
        raise ProviderError("Context must be >= 2048 and leave room for the prompt and output")
    local_api = setting("LOCAL_LLM_API", "auto").lower()
    if local_api not in {"auto", "ollama", "compatible"}:
        raise ProviderError("LOCAL_LLM_API must be auto, ollama, or compatible")

    return ProviderConfig(
        provider=provider,
        model=setting("LLM_MODEL", model_default),
        api_key=api_key,
        base_url=setting("LLM_BASE_URL", url_default).rstrip("/"),
        timeout_seconds=timeout_seconds,
        context_tokens=context_tokens,
        max_output_tokens=max_output_tokens,
        local_api=local_api,
    )


def _response_text(response_payload: dict[str, Any], provider: str) -> str:
    try:
        if provider == "ollama":
            if response_payload.get("done_reason") == "length":
                raise ProviderError("Model output reached the token limit before completion")
            content = response_payload["message"]["content"]
        elif provider in {"openai", "local"}:
            choice = response_payload["choices"][0]
            if choice.get("finish_reason") == "length":
                raise ProviderError("Model output reached the token limit before completion")
            content = choice["message"]["content"]
        else:
            if response_payload.get("stop_reason") == "max_tokens":
                raise ProviderError("Model output reached the token limit before completion")
            content = "".join(
                item.get("text", "") for item in response_payload["content"]
                if item.get("type") == "text"
            )
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("The model provider returned empty answer content")
        return content
    except (KeyError, IndexError, TypeError, AttributeError) as error:
        raise ProviderError("The model provider returned an unexpected response shape") from error


def generate_text(
    config: ProviderConfig, system_prompt: str, user_prompt: str,
    response_schema: dict[str, Any] | None = None,
) -> str:
    if config.provider == "none":
        raise ProviderError("No answer-generation provider is configured")
    if config.provider not in {"openai", "anthropic", "local"}:
        raise ProviderError("Unsupported answer-generation provider")

    if config.uses_ollama:
        endpoint = f"{config.base_url.rstrip('/').removesuffix('/v1')}/api/chat"
        payload = {
            "model": config.model,
            "stream": False,
            "format": response_schema or "json",
            "options": {"temperature": 0, "num_ctx": config.context_tokens,
                        "num_predict": config.max_output_tokens},
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": user_prompt}],
        }
        headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}
    elif config.provider == "anthropic":
        endpoint = f"{config.base_url}/messages"
        payload = {
            "model": config.model,
            "max_tokens": config.max_output_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": "2023-06-01",
        }
    else:
        endpoint = f"{config.base_url}/chat/completions"
        payload = {
            "model": config.model,
            "temperature": 0,
            "max_tokens": config.max_output_tokens,
            "response_format": (
                {"type": "json_schema", "json_schema": {
                    "name": "evidence_answer", "strict": True, "schema": response_schema,
                }} if response_schema else {"type": "json_object"}
            ),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            return _response_text(response_payload, "ollama" if config.uses_ollama else config.provider)
        except urllib.error.HTTPError as error:
            error_code = ""
            try:
                error_payload = json.loads(error.read().decode("utf-8"))
                error_code = str(error_payload.get("error", {}).get("code") or "")
            except (AttributeError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
                pass
            if error.code == 429 or 500 <= error.code < 600:
                if attempt < 2:
                    continue
            suffix = f" ({error_code})" if error_code else ""
            raise ProviderError(f"{config.provider} request failed with HTTP {error.code}{suffix}") from error
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise ProviderError(f"{config.provider} request failed: {error}") from error
    raise ProviderError(f"{config.provider} request failed after retries")
