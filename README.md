# key-checker

CLI tool to validate API keys for AI providers. Checks whether your keys are still active and working.

## Supported Providers

| Provider | Validation Method |
|----------|------------------|
| Anthropic | Sends a minimal 1-token completion request |
| OpenAI | Lists available models |
| Gemini | Lists available models |
| NVIDIA | Lists available models |
| OpenRouter | Queries key info and remaining credits |

## Installation

```bash
git clone https://github.com/skynergroup/key-checker.git
cd key-checker
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

### Pass keys directly

```bash
key-checker --anthropic sk-ant-xxx --openai sk-xxx --gemini AIza-xxx
```

### Use environment variables

```bash
export ANTHROPIC_API_KEY=sk-ant-xxx
export OPENAI_API_KEY=sk-xxx
export GEMINI_API_KEY=AIza-xxx
export NVIDIA_API_KEY=nvapi-xxx
export OPENROUTER_API_KEY=sk-or-xxx

key-checker
```

### Use a `.env` file

Create a `.env` file in the current directory (see `.env.example`):

```
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GEMINI_API_KEY=AIza-xxx
NVIDIA_API_KEY=nvapi-xxx
OPENROUTER_API_KEY=sk-or-xxx
```

Then run:

```bash
key-checker
```

### JSON output

```bash
key-checker --json
```

```json
[
  {
    "provider": "Anthropic",
    "valid": true,
    "status": "Valid",
    "detail": "claude-sonnet-4-20250514"
  },
  {
    "provider": "OpenAI",
    "valid": false,
    "status": "Invalid",
    "detail": "401"
  }
]
```

## Key Input Priority

Keys are resolved in this order (first match wins):

1. CLI arguments (`--anthropic KEY`)
2. `.env` file in the current directory
3. Environment variables

Only providers with a key present are checked. The rest are skipped silently.

## Status Codes

| Status | Meaning |
|--------|---------|
| Valid | Key is active and working |
| Valid (rate limited) | Key is valid but currently rate limited (429) |
| Invalid | Key was rejected (401/403) |
| Unreachable | Could not connect to the provider |
| Timeout | Provider did not respond within 5 seconds |

## Exit Codes

- `0` — all checked keys are valid
- `1` — one or more keys are invalid, or no keys were found

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
