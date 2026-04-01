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
        value = (
            cli_args.get(provider)
            or dotenv_keys.get(env_var)
            or os.environ.get(env_var)
        )
        if value:
            keys[provider] = value

    return keys
