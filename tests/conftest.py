"""Shared test fixtures for CLI tests."""
import json
from pathlib import Path

import pytest

from viral_cli.config import CliConfig


@pytest.fixture()
def mock_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect config to temp dir."""
    config_path = tmp_path / ".viralanalyzer" / "config.json"
    monkeypatch.setattr("viral_cli.config.get_config_path", lambda: config_path)
    return config_path


@pytest.fixture()
def saved_config(mock_config_dir: Path) -> CliConfig:
    """Pre-save a config with test API key."""
    cfg = CliConfig(api_key="va_live_test123", api_url="https://test.local")
    mock_config_dir.parent.mkdir(parents=True, exist_ok=True)
    mock_config_dir.write_text(cfg.model_dump_json(indent=2), encoding="utf-8")
    return cfg


# -- Sample API responses for mocking --

SAMPLE_CONTENT_LIST = {
    "data": [
        {
            "id": 1,
            "platform": "youtube",
            "profile_username": "testuser",
            "content_type": "video",
            "title": "Test Video",
            "url": "https://youtube.com/watch?v=123",
            "published_at": "2026-03-15T10:00:00Z",
            "metrics": {"views": 1000, "likes": 50, "engagement_rate": 0.05},
            "analysis": {"viral_score": 7.5, "sentiment": "positive"},
        }
    ],
    "total": 1,
}

SAMPLE_USER = {
    "name": "Test User",
    "email": "test@test.com",
    "company": "TestCo",
    "plan": "starter",
    "calls_used": 50,
    "calls_limit": 1000,
    "status": "active",
}

SAMPLE_USAGE = {
    "plan_name": "starter",
    "calls_used": 50,
    "calls_limit": 1000,
    "pct_used": 5.0,
    "status": "active",
    "expires_at": "2026-04-15T00:00:00Z",
    "executions_used": 5,
    "executions_limit": 30,
    "executions_pct": 16.7,
    "overage_total_brl": 0.0,
    "overage_details": [],
}

SAMPLE_IDEAS_LIFECYCLE = {
    "total": 50,
    "by_status": {
        "generated": 40,
        "reviewed": 5,
        "in_production": 3,
        "published": 2,
        "discarded": 0,
    },
}
