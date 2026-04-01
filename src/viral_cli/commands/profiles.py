"""Profiles commands: list, add, delete."""
import typer
from rich.console import Console

from viral_cli.client import ViralClient
from viral_cli.constants import API
from viral_cli.errors import handle_error
from viral_cli.output import OutputFormat, render

app = typer.Typer(no_args_is_help=True)
console = Console()

COLUMNS = [
    ("id", "ID"),
    ("username", "Username"),
    ("display_name", "Display Name"),
    ("platform", "Platform"),
    ("category", "Category"),
    ("followers", "Followers"),
    ("is_active", "Active"),
]


@app.command("list")
def list_profiles(
    platform: str = typer.Option(None, "--platform", "-p"),
    category: str = typer.Option(None, "--category", "-c"),
    include_inactive: bool = typer.Option(False, "--inactive", help="Include deactivated"),
    limit: int = typer.Option(50, "--limit", "-n"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """List monitored profiles."""
    try:
        client = ViralClient()
        params: dict = {"limit": limit, "active_only": not include_inactive}
        if platform:
            params["platform"] = platform
        if category:
            params["category"] = category

        data = client.get(API.PROFILES, params=params)
        items = data if isinstance(data, list) else data.get("data", [])
        render(items, fmt, columns=COLUMNS, title="Monitored Profiles")
    except Exception as e:
        handle_error(e)


@app.command("add")
def add_profile(
    platform: str = typer.Argument(..., help="Platform: tiktok, youtube, instagram, ..."),
    username: str = typer.Argument(..., help="Profile username"),
    display_name: str = typer.Option(None, "--name"),
    url: str = typer.Option(None, "--url"),
    category: str = typer.Option(None, "--category", "-c"),
) -> None:
    """Add a new profile to monitor."""
    try:
        client = ViralClient()
        body: dict = {"platform": platform, "username": username}
        if display_name:
            body["display_name"] = display_name
        if url:
            body["url"] = url
        if category:
            body["category"] = category

        client.post(API.PROFILES, json_body=body)
        console.print(f"[green]Profile added:[/] {username} on {platform}")
    except Exception as e:
        handle_error(e)


@app.command("delete")
def delete_profile(
    profile_id: int = typer.Argument(..., help="Profile ID to deactivate"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Deactivate a monitored profile."""
    if not confirm:
        typer.confirm(f"Deactivate profile {profile_id}?", abort=True)
    try:
        client = ViralClient()
        client.delete(f"{API.PROFILES}/{profile_id}")
        console.print(f"[yellow]Profile {profile_id} deactivated.[/]")
    except Exception as e:
        handle_error(e)
