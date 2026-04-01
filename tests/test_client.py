"""Tests for the HTTP API client."""
import httpx
import pytest
import respx

from viral_cli.client import ViralClient
from viral_cli.config import CliConfig
from viral_cli.errors import AuthenticationError, RateLimitError, ViralApiError


def _client(api_url: str = "https://test.local") -> ViralClient:
    return ViralClient(config=CliConfig(api_key="va_live_test", api_url=api_url))


@respx.mock
def test_get_injects_auth_header() -> None:
    """Client sends X-API-Key header."""
    route = respx.get("https://test.local/api/v1/test").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    client = _client()
    result = client.get("/api/v1/test")
    assert result == {"ok": True}
    assert route.called
    sent_key = route.calls[0].request.headers.get("x-api-key")
    assert sent_key == "va_live_test"


@respx.mock
def test_401_raises_auth_error() -> None:
    """401 response raises AuthenticationError."""
    respx.get("https://test.local/test").mock(
        return_value=httpx.Response(401, json={"detail": "Invalid key"})
    )
    client = _client()
    with pytest.raises(AuthenticationError, match="Invalid key"):
        client.get("/test")


@respx.mock
def test_429_raises_rate_limit() -> None:
    """429 response raises RateLimitError after retries."""
    respx.get("https://test.local/test").mock(
        return_value=httpx.Response(429, json={"detail": "Rate limit"})
    )
    client = _client()
    with pytest.raises(RateLimitError, match="Rate limit"):
        client.get("/test")


@respx.mock
def test_500_raises_api_error() -> None:
    """5xx response raises ViralApiError."""
    respx.get("https://test.local/test").mock(
        return_value=httpx.Response(500, json={"detail": "Internal error"})
    )
    client = _client()
    with pytest.raises(ViralApiError, match="Internal error"):
        client.get("/test")


def test_no_api_key_raises_auth_error() -> None:
    """Client without API key raises immediately."""
    with pytest.raises(AuthenticationError, match="No API key"):
        ViralClient(config=CliConfig(api_key=""))


@respx.mock
def test_post_sends_json() -> None:
    """POST sends JSON body."""
    route = respx.post("https://test.local/api/v1/create").mock(
        return_value=httpx.Response(200, json={"id": 1})
    )
    client = _client()
    result = client.post("/api/v1/create", json_body={"name": "test"})
    assert result == {"id": 1}
    sent_body = route.calls[0].request.content
    assert b'"name"' in sent_body


@respx.mock
def test_delete_returns_none() -> None:
    """DELETE with 204 returns None."""
    respx.delete("https://test.local/api/v1/items/1").mock(
        return_value=httpx.Response(204)
    )
    client = _client()
    result = client.delete("/api/v1/items/1")
    assert result is None
