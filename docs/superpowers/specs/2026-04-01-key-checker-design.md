# Key Checker — Design Spec

## Overview

Python CLI tool that validates API keys for AI providers by making lightweight API calls. Checks Anthropic, OpenAI, Gemini, NVIDIA, and OpenRouter.

## Validation Strategy

| Provider   | Endpoint                         | Method          | What it proves              |
|------------|----------------------------------|-----------------|-----------------------------|
| Anthropic  | `POST /v1/messages` (1 token)    | Tiny completion | Key valid, model access     |
| OpenAI     | `GET /v1/models`                 | List models     | Key valid, no cost          |
| Gemini     | `GET /v1beta/models`             | List models     | Key valid, no cost          |
| NVIDIA     | `GET /v1/models`                 | List models     | Key valid, no cost          |
| OpenRouter | `GET /api/v1/auth/key`           | Key info        | Key valid, credits remaining|

## Key Input (priority order)

1. CLI args: `--anthropic KEY`, `--openai KEY`, etc.
2. `.env` file in current directory
3. Environment variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `NVIDIA_API_KEY`, `OPENROUTER_API_KEY`

Only checks providers whose keys are found. Skips the rest silently.

## Output

- Default: colored terminal table (using `rich`)
- `--json` flag: JSON array of results
- Exit code 0 if all checked keys valid, 1 if any invalid

## Dependencies

- `httpx` — async HTTP client
- `rich` — terminal table/colors
- `python-dotenv` — .env file loading

## Project Structure

```
key-checker/
├── pyproject.toml        # packaging, CLI entry point, dependencies
├── key_checker.py        # single module — all logic
└── .env.example          # template showing expected var names
```

## Error Handling

- Network errors: "Unreachable" status
- 401/403: "Invalid"
- 429: "Valid (rate limited)"
- Timeout (5s per provider): "Timeout"

## Exit Codes

- 0: all checked keys are valid
- 1: one or more keys invalid or errored
