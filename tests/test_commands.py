"""Integration tests for CLI commands using Typer CliRunner."""
import httpx
import respx
from typer.testing import CliRunner

from viral_cli.app import app

runner = CliRunner()


def test_version() -> None:
    """--version prints version string."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "viral-analyzer-cli" in result.output


def test_help() -> None:
    """--help shows all command groups."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "auth" in result.output
    assert "content" in result.output
    assert "ideas" in result.output
    assert "billing" in result.output


@respx.mock
def test_auth_me(saved_config) -> None:
    """viral auth me displays user info."""
    respx.get("https://test.local/api/v1/auth/me").mock(
        return_value=httpx.Response(200, json={
            "name": "Test User", "email": "test@test.com", "company": "Co",
            "plan": "starter", "calls_used": 50, "calls_limit": 1000, "status": "active",
        })
    )
    result = runner.invoke(app, ["auth", "me"])
    assert result.exit_code == 0
    assert "Test User" in result.output
    assert "starter" in result.output


@respx.mock
def test_content_list(saved_config) -> None:
    """viral content list shows table."""
    respx.get("https://test.local/api/v1/content").mock(
        return_value=httpx.Response(200, json={
            "data": [{
                "id": 1, "platform": "youtube", "profile_username": "user",
                "content_type": "video", "title": "Test Video",
                "metrics": {"views": 5000, "likes": 100},
                "analysis": {"viral_score": 8},
            }],
            "total": 1,
        })
    )
    result = runner.invoke(app, ["content", "list", "--limit", "5"])
    assert result.exit_code == 0
    assert "youtube" in result.output
    assert "Test Video" in result.output


@respx.mock
def test_billing_usage(saved_config) -> None:
    """viral billing usage shows plan info."""
    respx.get("https://test.local/api/v1/billing/usage").mock(
        return_value=httpx.Response(200, json={
            "plan_name": "business", "calls_used": 200, "calls_limit": 5000,
            "pct_used": 4.0, "status": "active", "expires_at": "2026-05-01",
            "executions_used": 10, "executions_limit": 100, "executions_pct": 10.0,
            "overage_total_brl": 0, "overage_details": [],
        })
    )
    result = runner.invoke(app, ["billing", "usage"])
    assert result.exit_code == 0
    assert "BUSINESS" in result.output
    assert "200/5000" in result.output


@respx.mock
def test_ideas_summary(saved_config) -> None:
    """viral ideas summary shows lifecycle counts."""
    respx.get("https://test.local/api/v1/ideas/lifecycle/summary").mock(
        return_value=httpx.Response(200, json={
            "total": 50,
            "by_status": {"generated": 40, "reviewed": 5, "published": 3, "discarded": 2},
        })
    )
    result = runner.invoke(app, ["ideas", "summary"])
    assert result.exit_code == 0
    assert "generated" in result.output
    assert "40" in result.output
