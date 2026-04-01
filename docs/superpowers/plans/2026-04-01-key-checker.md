# Key Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that validates API keys for Anthropic, OpenAI, Gemini, NVIDIA, and OpenRouter.

**Architecture:** Single-file Python module (`key_checker.py`) with async HTTP checks running concurrently via `httpx`. CLI parsing with `argparse`. Output via `rich` tables or JSON. Keys loaded from CLI args, `.env` file, or environment variables (in that priority order).

**Tech Stack:** Python 3.10+, httpx, rich, python-dotenv, pytest, respx (HTTP mocking)

---

## File Structure

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Package metadata, dependencies, CLI entry point (`key-checker`) |
| `key_checker.py` | All logic: key loading, provider checks, output formatting, CLI |
| `.env.example` | Template showing expected environment variable names |
| `tests/test_key_checker.py` | All tests: key loading, provider checks, output, CLI |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "key-checker"
version = "0.1.0"
description = "CLI tool to validate API keys for AI providers"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.27",
    "rich>=13.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "respx>=0.22",
]

[project.scripts]
key-checker = "key_checker:main"
```

- [ ] **Step 2: Create .env.example**

```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
NVIDIA_API_KEY=
OPENROUTER_API_KEY=
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.egg-info/
dist/
.env
.venv/
```

- [ ] **Step 4: Install project in dev mode**

Run: `cd /Users/yashielsookdeo/Developer/ai-tools/key-checker && python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
Expected: Successful install with all dependencies

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example .gitignore
git commit -m "feat: scaffold project with dependencies and CLI entry point"
```

---

### Task 2: Key Loading

**Files:**
- Create: `tests/test_key_checker.py`
- Create: `key_checker.py`

- [ ] **Step 1: Write failing tests for key loading**

```python
# tests/test_key_checker.py
import os
import pytest
from unittest.mock import patch
from key_checker import load_keys, PROVIDERS


def test_load_keys_from_env():
    env = {"ANTHROPIC_API_KEY": "sk-ant-test123"}
    with patch.dict(os.environ, env, clear=False):
        keys = load_keys(cli_args={})
    assert keys["anthropic"] == "sk-ant-test123"


def test_load_keys_cli_overrides_env():
    env = {"ANTHROPIC_API_KEY": "from-env"}
    cli = {"anthropic": "from-cli"}
    with patch.dict(os.environ, env, clear=False):
        keys = load_keys(cli_args=cli)
    assert keys["anthropic"] == "from-cli"


def test_load_keys_skips_missing():
    with patch.dict(os.environ, {}, clear=True):
        keys = load_keys(cli_args={})
    assert keys == {}


def test_load_keys_from_dotenv(tmp_path):
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("OPENAI_API_KEY=sk-dotenv-test\n")
    with patch.dict(os.environ, {}, clear=True):
        keys = load_keys(cli_args={}, dotenv_path=str(dotenv_file))
    assert keys["openai"] == "sk-dotenv-test"


def test_cli_overrides_dotenv(tmp_path):
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("OPENAI_API_KEY=sk-dotenv\n")
    cli = {"openai": "sk-cli"}
    with patch.dict(os.environ, {}, clear=True):
        keys = load_keys(cli_args=cli, dotenv_path=str(dotenv_file))
    assert keys["openai"] == "sk-cli"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/yashielsookdeo/Developer/ai-tools/key-checker && source .venv/bin/activate && pytest tests/test_key_checker.py -v`
Expected: FAIL — `key_checker` module has no `load_keys`

- [ ] **Step 3: Implement key loading**

```python
# key_checker.py
from __future__ import annotations

import os
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
        # Priority: CLI > .env > env var
        value = (
            cli_args.get(provider)
            or dotenv_keys.get(env_var)
            or os.environ.get(env_var)
        )
        if value:
            keys[provider] = value

    return keys
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_key_checker.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add key_checker.py tests/test_key_checker.py
git commit -m "feat: add key loading with CLI > .env > env var priority"
```

---

### Task 3: Provider Check Functions

**Files:**
- Modify: `tests/test_key_checker.py`
- Modify: `key_checker.py`

- [ ] **Step 1: Write failing tests for provider checks**

Append to `tests/test_key_checker.py`:

```python
import httpx
import respx
from key_checker import check_anthropic, check_openai, check_gemini, check_nvidia, check_openrouter, CheckResult


@pytest.mark.asyncio
async def test_check_openai_valid():
    with respx.mock:
        respx.get("https://api.openai.com/v1/models").mock(
            return_value=httpx.Response(200, json={"data": [{"id": "gpt-4o"}]})
        )
        result = await check_openai("sk-test")
    assert result.valid is True
    assert result.status == "Valid"


@pytest.mark.asyncio
async def test_check_openai_invalid():
    with respx.mock:
        respx.get("https://api.openai.com/v1/models").mock(
            return_value=httpx.Response(401, json={"error": {"message": "Invalid API key"}})
        )
        result = await check_openai("sk-bad")
    assert result.valid is False
    assert result.status == "Invalid"


@pytest.mark.asyncio
async def test_check_anthropic_valid():
    with respx.mock:
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(200, json={
                "content": [{"type": "text", "text": "hi"}],
                "model": "claude-sonnet-4-20250514",
            })
        )
        result = await check_anthropic("sk-ant-test")
    assert result.valid is True
    assert result.status == "Valid"


@pytest.mark.asyncio
async def test_check_anthropic_invalid():
    with respx.mock:
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(401, json={"error": {"message": "Invalid API key"}})
        )
        result = await check_anthropic("sk-ant-bad")
    assert result.valid is False
    assert result.status == "Invalid"


@pytest.mark.asyncio
async def test_check_gemini_valid():
    with respx.mock:
        respx.get("https://generativelanguage.googleapis.com/v1beta/models").mock(
            return_value=httpx.Response(200, json={"models": [{"name": "models/gemini-2.0-flash"}]})
        )
        result = await check_gemini("AIza-test")
    assert result.valid is True
    assert result.status == "Valid"


@pytest.mark.asyncio
async def test_check_gemini_invalid():
    with respx.mock:
        respx.get("https://generativelanguage.googleapis.com/v1beta/models").mock(
            return_value=httpx.Response(403, json={"error": {"message": "API key not valid"}})
        )
        result = await check_gemini("AIza-bad")
    assert result.valid is False
    assert result.status == "Invalid"


@pytest.mark.asyncio
async def test_check_nvidia_valid():
    with respx.mock:
        respx.get("https://integrate.api.nvidia.com/v1/models").mock(
            return_value=httpx.Response(200, json={"data": [{"id": "meta/llama-3.1-8b-instruct"}]})
        )
        result = await check_nvidia("nvapi-test")
    assert result.valid is True
    assert result.status == "Valid"


@pytest.mark.asyncio
async def test_check_nvidia_invalid():
    with respx.mock:
        respx.get("https://integrate.api.nvidia.com/v1/models").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )
        result = await check_nvidia("nvapi-bad")
    assert result.valid is False
    assert result.status == "Invalid"


@pytest.mark.asyncio
async def test_check_openrouter_valid():
    with respx.mock:
        respx.get("https://openrouter.ai/api/v1/auth/key").mock(
            return_value=httpx.Response(200, json={
                "data": {"label": "test", "limit": 10.0, "usage": 2.5}
            })
        )
        result = await check_openrouter("sk-or-test")
    assert result.valid is True
    assert "$7.50 credits remaining" in result.detail


@pytest.mark.asyncio
async def test_check_openrouter_invalid():
    with respx.mock:
        respx.get("https://openrouter.ai/api/v1/auth/key").mock(
            return_value=httpx.Response(401, json={"error": "Invalid key"})
        )
        result = await check_openrouter("sk-or-bad")
    assert result.valid is False
    assert result.status == "Invalid"


@pytest.mark.asyncio
async def test_check_network_error():
    with respx.mock:
        respx.get("https://api.openai.com/v1/models").mock(side_effect=httpx.ConnectError("Connection refused"))
        result = await check_openai("sk-test")
    assert result.valid is False
    assert result.status == "Unreachable"


@pytest.mark.asyncio
async def test_check_rate_limited():
    with respx.mock:
        respx.get("https://api.openai.com/v1/models").mock(
            return_value=httpx.Response(429, json={"error": {"message": "Rate limited"}})
        )
        result = await check_openai("sk-test")
    assert result.valid is True
    assert result.status == "Valid (rate limited)"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_key_checker.py -v`
Expected: FAIL — `check_openai`, `check_anthropic`, etc. not defined

- [ ] **Step 3: Implement CheckResult and provider check functions**

Add to `key_checker.py`:

```python
import asyncio
from dataclasses import dataclass

import httpx


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_key_checker.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add key_checker.py tests/test_key_checker.py
git commit -m "feat: add async provider check functions with error handling"
```

---

### Task 4: Output Formatting

**Files:**
- Modify: `tests/test_key_checker.py`
- Modify: `key_checker.py`

- [ ] **Step 1: Write failing tests for output formatting**

Append to `tests/test_key_checker.py`:

```python
import json
from key_checker import format_json, format_table


def test_format_json():
    results = [
        CheckResult(provider="OpenAI", valid=True, status="Valid", detail="gpt-4o"),
        CheckResult(provider="Gemini", valid=False, status="Invalid", detail="403"),
    ]
    output = format_json(results)
    parsed = json.loads(output)
    assert len(parsed) == 2
    assert parsed[0]["provider"] == "OpenAI"
    assert parsed[0]["valid"] is True
    assert parsed[1]["valid"] is False


def test_format_table():
    results = [
        CheckResult(provider="OpenAI", valid=True, status="Valid", detail="gpt-4o"),
    ]
    output = format_table(results)
    assert "OpenAI" in output
    assert "Valid" in output
    assert "gpt-4o" in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_key_checker.py::test_format_json tests/test_key_checker.py::test_format_table -v`
Expected: FAIL — `format_json`, `format_table` not defined

- [ ] **Step 3: Implement output formatting**

Add to `key_checker.py`:

```python
import json as json_mod
from io import StringIO
from rich.console import Console
from rich.table import Table


def format_json(results: list[CheckResult]) -> str:
    return json_mod.dumps(
        [
            {
                "provider": r.provider,
                "valid": r.valid,
                "status": r.status,
                "detail": r.detail,
            }
            for r in results
        ],
        indent=2,
    )


def format_table(results: list[CheckResult]) -> str:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Provider", style="cyan", min_width=12)
    table.add_column("Status", min_width=10)
    table.add_column("Detail")

    for r in results:
        if r.valid:
            status = f"[green]✓ {r.status}[/green]"
        else:
            status = f"[red]✗ {r.status}[/red]"
        table.add_row(r.provider, status, r.detail)

    buf = StringIO()
    console = Console(file=buf, force_terminal=True)
    console.print(table)
    return buf.getvalue()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_key_checker.py::test_format_json tests/test_key_checker.py::test_format_table -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add key_checker.py tests/test_key_checker.py
git commit -m "feat: add table and JSON output formatting"
```

---

### Task 5: CLI Entry Point

**Files:**
- Modify: `tests/test_key_checker.py`
- Modify: `key_checker.py`

- [ ] **Step 1: Write failing tests for CLI**

Append to `tests/test_key_checker.py`:

```python
from unittest.mock import AsyncMock
from key_checker import build_parser


def test_build_parser_provider_args():
    parser = build_parser()
    args = parser.parse_args(["--anthropic", "sk-test", "--json"])
    assert args.anthropic == "sk-test"
    assert args.json is True


def test_build_parser_no_args():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.anthropic is None
    assert args.json is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_key_checker.py::test_build_parser_provider_args tests/test_key_checker.py::test_build_parser_no_args -v`
Expected: FAIL — `build_parser` not defined

- [ ] **Step 3: Implement CLI entry point**

Add to `key_checker.py`:

```python
import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="key-checker",
        description="Validate API keys for AI providers",
    )
    parser.add_argument("--anthropic", metavar="KEY", help="Anthropic API key")
    parser.add_argument("--openai", metavar="KEY", help="OpenAI API key")
    parser.add_argument("--gemini", metavar="KEY", help="Gemini API key")
    parser.add_argument("--nvidia", metavar="KEY", help="NVIDIA API key")
    parser.add_argument("--openrouter", metavar="KEY", help="OpenRouter API key")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    cli_args = {
        name: getattr(args, name)
        for name in PROVIDERS
        if getattr(args, name) is not None
    }

    keys = load_keys(cli_args)

    if not keys:
        print("No API keys found. Provide keys via CLI args, .env file, or environment variables.")
        sys.exit(1)

    results = asyncio.run(check_all(keys))

    if args.json:
        print(format_json(results))
    else:
        print(format_table(results))

    if any(not r.valid for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_key_checker.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add key_checker.py tests/test_key_checker.py
git commit -m "feat: add CLI entry point with argparse"
```

---

### Task 6: End-to-End Smoke Test & Push

**Files:**
- No new files

- [ ] **Step 1: Run full test suite**

Run: `pytest tests/test_key_checker.py -v`
Expected: All tests PASS

- [ ] **Step 2: Verify CLI help works**

Run: `source .venv/bin/activate && key-checker --help`
Expected: Shows usage with all provider flags and --json

- [ ] **Step 3: Verify CLI runs with no keys (exits 1 with message)**

Run: `env -i key-checker 2>&1; echo "exit: $?"`
Expected: "No API keys found" message, exit code 1

- [ ] **Step 4: Push to remote**

```bash
git push -u origin main
```
