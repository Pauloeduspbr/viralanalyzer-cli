"""Tests for config management."""
import json
from pathlib import Path

from viral_cli.config import CliConfig, clear_config, load_config, save_config


def test_load_missing_config(mock_config_dir: Path) -> None:
    """Missing config returns defaults."""
    cfg = load_config()
    assert cfg.api_key == ""
    assert cfg.api_url == "https://api.viralanalyzer.com.br"
    assert cfg.default_format == "table"


def test_save_and_load(mock_config_dir: Path) -> None:
    """Round-trip save and load."""
    cfg = CliConfig(api_key="va_live_abc", api_url="https://staging.test")
    save_config(cfg)
    loaded = load_config()
    assert loaded.api_key == "va_live_abc"
    assert loaded.api_url == "https://staging.test"


def test_clear_config(mock_config_dir: Path) -> None:
    """Clear removes the file."""
    cfg = CliConfig(api_key="va_live_xyz")
    save_config(cfg)
    assert mock_config_dir.exists()
    clear_config()
    assert not mock_config_dir.exists()


def test_corrupt_config_returns_defaults(mock_config_dir: Path) -> None:
    """Corrupt JSON returns defaults."""
    mock_config_dir.parent.mkdir(parents=True, exist_ok=True)
    mock_config_dir.write_text("not json!!!", encoding="utf-8")
    cfg = load_config()
    assert cfg.api_key == ""
