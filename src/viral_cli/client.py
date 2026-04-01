"""
Authenticated httpx client for the ViralAnalyzer API.

All methods return the parsed JSON dict or raise ViralApiError.
Handles:
  - Auth header injection (X-API-Key)
  - Base URL construction
  - HTTP error -> ViralApiError mapping
  - Pagination via generator
  - Retry on 429/5xx with backoff
"""
import time
from typing import Any, Generator

import httpx

from viral_cli.config import CliConfig, load_config
from viral_cli.constants import APP_VERSION
from viral_cli.errors import AuthenticationError, RateLimitError, ViralApiError

_RETRY_STATUS = {429, 502, 503, 504}
_MAX_RETRIES = 3


class ViralClient:
    """Synchronous API client with retry and error mapping."""

    def __init__(self, config: CliConfig | None = None):
        self._config = config or load_config()
        if not self._config.api_key:
            raise AuthenticationError(
                "No API key configured. Run 'viral auth login' first."
            )
        self._http = httpx.Client(
            base_url=self._config.api_url,
            headers={
                "X-API-Key": self._config.api_key,
                "User-Agent": f"viral-cli/{APP_VERSION}",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return self._request("POST", path, json=json_body, params=params)

    def patch(self, path: str, json_body: dict[str, Any]) -> Any:
        return self._request("PATCH", path, json=json_body)

    def delete(self, path: str) -> None:
        self._request("DELETE", path)

    def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        limit: int = 50,
        max_items: int | None = None,
    ) -> Generator[dict, None, None]:
        """Yield items from a paginated endpoint ({data: [...], total: N})."""
        params = dict(params or {})
        offset = 0
        yielded = 0
        while True:
            params["limit"] = limit
            params["offset"] = offset
            resp = self.get(path, params=params)
            items = resp.get("data", []) if isinstance(resp, dict) else resp
            if not items:
                break
            for item in items:
                yield item
                yielded += 1
                if max_items and yielded >= max_items:
                    return
            offset += len(items)
            total = resp.get("total", 0) if isinstance(resp, dict) else 0
            if total and offset >= total:
                break

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Execute request with retry logic and error mapping."""
        last_resp = None
        for attempt in range(_MAX_RETRIES):
            try:
                resp = self._http.request(method, path, **kwargs)
            except httpx.ConnectError as e:
                raise ViralApiError(
                    f"Cannot connect to {self._config.api_url}: {e}"
                ) from e

            if resp.status_code < 400:
                if resp.status_code == 204:
                    return None
                return resp.json()

            if resp.status_code in _RETRY_STATUS and attempt < _MAX_RETRIES - 1:
                wait = (2**attempt) * 0.5
                time.sleep(wait)
                last_resp = resp
                continue

            self._raise_for_status(resp)

        if last_resp is not None:
            self._raise_for_status(last_resp)
        raise ViralApiError("Max retries exceeded")

    def _raise_for_status(self, resp: httpx.Response) -> None:
        """Map HTTP error to typed exception."""
        detail = ""
        try:
            body = resp.json()
            detail = body.get("detail", str(body))
        except Exception:
            detail = resp.text

        if resp.status_code == 401:
            raise AuthenticationError(detail)
        if resp.status_code == 429:
            raise RateLimitError(detail)
        raise ViralApiError(detail, status_code=resp.status_code)

    def close(self) -> None:
        self._http.close()
