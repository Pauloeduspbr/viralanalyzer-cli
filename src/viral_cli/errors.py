"""CLI error types mapped from API HTTP responses."""
import sys

from rich.console import Console

err_console = Console(stderr=True)


class ViralApiError(Exception):
    """Generic API error with optional HTTP status code."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(ViralApiError):
    """401 — bad or missing credentials."""


class RateLimitError(ViralApiError):
    """429 — plan limit exceeded."""


def handle_error(e: Exception) -> None:
    """Print a user-friendly error to stderr and exit."""
    if isinstance(e, AuthenticationError):
        err_console.print(
            "[bold red]Authentication failed.[/] "
            "Run [cyan]viral auth login[/] first."
        )
        err_console.print(f"  Detail: {e.message}")
        sys.exit(1)
    elif isinstance(e, RateLimitError):
        err_console.print(
            "[bold yellow]Rate limit reached.[/] "
            "Your plan's API call limit has been exceeded."
        )
        err_console.print(f"  Detail: {e.message}")
        err_console.print(
            "  Run [cyan]viral billing usage[/] to check your current usage."
        )
        sys.exit(1)
    elif isinstance(e, ViralApiError):
        err_console.print(
            f"[bold red]API Error[/] (HTTP {e.status_code}): {e.message}"
        )
        sys.exit(1)
    else:
        err_console.print(f"[bold red]Unexpected error:[/] {e}")
        sys.exit(1)
