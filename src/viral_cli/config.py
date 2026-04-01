"""
Config manager for ~/.viralanalyzer/config.json

Schema:
{
    "api_key": "va_live_...",
    "api_url": "https://api.viralanalyzer.com.br",
    "default_format": "table"
}
"""
import json
import os
import stat
from pathlib import Path

from pydantic import BaseModel

from viral_cli.constants import CONFIG_DIR_NAME, CONFIG_FILE_NAME, DEFAULT_API_URL


class CliConfig(BaseModel):
    api_key: str = ""
    api_url: str = DEFAULT_API_URL
    default_format: str = "table"


def get_config_path() -> Path:
    """Return the path to the config file."""
    return Path.home() / CONFIG_DIR_NAME / CONFIG_FILE_NAME


def load_config() -> CliConfig:
    """Load config from disk, return defaults if missing."""
    path = get_config_path()
    if not path.exists():
        return CliConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return CliConfig(**data)
    except (json.JSONDecodeError, ValueError):
        return CliConfig()


def save_config(config: CliConfig) -> None:
    """Persist config to disk, creating directory if needed."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except OSError:
        pass  # Windows may not support chmod


def clear_config() -> None:
    """Remove stored credentials (logout)."""
    path = get_config_path()
    if path.exists():
        path.unlink()
