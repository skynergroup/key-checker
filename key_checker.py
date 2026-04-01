from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

import httpx
from dotenv import dotenv_values

PROVIDERS = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def load_keys(
    cli_args: dict[str, str | None],
    dotenv_path: str = ".env",
) -> dict[str, str]:
    """Load API keys with priority: CLI args > .env file > environment variables."""
    dotenv_keys = dotenv_values(dotenv_path)
    keys: dict[str, str] = {}

    for provider, env_var in PROVIDERS.items():
        value = (
            cli_args.get(provider)
            or dotenv_keys.get(env_var)
            or os.environ.get(env_var)
        )
        if value:
            keys[provider] = value

    return keys


TIMEOUT = 5.0


@dataclass
class CheckResult:
    provider: str
    valid: bool
    status: str
    detail: str = ""


async def check_openai(key: str) -> CheckResult:
    return await _check_models_endpoint(
        provider="OpenAI",
        url="https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {key}"},
        model_path=lambda data: data.get("data", [{}])[0].get("id", ""),
    )


async def check_gemini(key: str) -> CheckResult:
    return await _check_models_endpoint(
        provider="Gemini",
        url="https://generativelanguage.googleapis.com/v1beta/models",
        headers={},
        params={"key": key},
        model_path=lambda data: data.get("models", [{}])[0].get("name", "").removeprefix("models/"),
    )


async def check_nvidia(key: str) -> CheckResult:
    return await _check_models_endpoint(
        provider="NVIDIA",
        url="https://integrate.api.nvidia.com/v1/models",
        headers={"Authorization": f"Bearer {key}"},
        model_path=lambda data: data.get("data", [{}])[0].get("id", ""),
    )


async def _check_models_endpoint(
    provider: str,
    url: str,
    headers: dict[str, str],
    model_path: callable,
    params: dict[str, str] | None = None,
) -> CheckResult:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, headers=headers, params=params)
        if resp.status_code == 429:
            return CheckResult(provider=provider, valid=True, status="Valid (rate limited)")
        if resp.status_code in (401, 403):
            return CheckResult(provider=provider, valid=False, status="Invalid", detail=f"{resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        model = model_path(data)
        return CheckResult(provider=provider, valid=True, status="Valid", detail=model)
    except httpx.ConnectError:
        return CheckResult(provider=provider, valid=False, status="Unreachable")
    except httpx.TimeoutException:
        return CheckResult(provider=provider, valid=False, status="Timeout")
    except httpx.HTTPStatusError as e:
        return CheckResult(provider=provider, valid=False, status="Error", detail=str(e.response.status_code))


async def check_anthropic(key: str) -> CheckResult:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )
        if resp.status_code == 429:
            return CheckResult(provider="Anthropic", valid=True, status="Valid (rate limited)")
        if resp.status_code in (401, 403):
            return CheckResult(provider="Anthropic", valid=False, status="Invalid", detail=f"{resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        model = data.get("model", "")
        return CheckResult(provider="Anthropic", valid=True, status="Valid", detail=model)
    except httpx.ConnectError:
        return CheckResult(provider="Anthropic", valid=False, status="Unreachable")
    except httpx.TimeoutException:
        return CheckResult(provider="Anthropic", valid=False, status="Timeout")
    except httpx.HTTPStatusError as e:
        return CheckResult(provider="Anthropic", valid=False, status="Error", detail=str(e.response.status_code))


async def check_openrouter(key: str) -> CheckResult:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {key}"},
            )
        if resp.status_code == 429:
            return CheckResult(provider="OpenRouter", valid=True, status="Valid (rate limited)")
        if resp.status_code in (401, 403):
            return CheckResult(provider="OpenRouter", valid=False, status="Invalid", detail=f"{resp.status_code}")
        resp.raise_for_status()
        data = resp.json().get("data", {})
        limit = data.get("limit")
        usage = data.get("usage", 0)
        if limit is not None:
            remaining = limit - usage
            detail = f"${remaining:.2f} credits remaining"
        else:
            detail = "unlimited"
        return CheckResult(provider="OpenRouter", valid=True, status="Valid", detail=detail)
    except httpx.ConnectError:
        return CheckResult(provider="OpenRouter", valid=False, status="Unreachable")
    except httpx.TimeoutException:
        return CheckResult(provider="OpenRouter", valid=False, status="Timeout")
    except httpx.HTTPStatusError as e:
        return CheckResult(provider="OpenRouter", valid=False, status="Error", detail=str(e.response.status_code))


CHECKERS = {
    "anthropic": check_anthropic,
    "openai": check_openai,
    "gemini": check_gemini,
    "nvidia": check_nvidia,
    "openrouter": check_openrouter,
}


async def check_all(keys: dict[str, str]) -> list[CheckResult]:
    tasks = [CHECKERS[provider](key) for provider, key in keys.items()]
    return await asyncio.gather(*tasks)
