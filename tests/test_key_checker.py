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
