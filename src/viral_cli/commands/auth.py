"""Auth commands: login, register, me, logout, config."""
import typer
from rich.console import Console

from viral_cli.client import ViralClient
from viral_cli.config import (
    CliConfig,
    clear_config,
    get_config_path,
    load_config,
    save_config,
)
from viral_cli.constants import API, DEFAULT_API_URL
from viral_cli.errors import AuthenticationError, handle_error
from viral_cli.output import OutputFormat, render

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def login(
    api_key: str = typer.Option(
        ..., prompt=True, help="Your API key (va_live_...)"
    ),
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url", help="API base URL"),
) -> None:
    """Login with an API key. Validates and stores locally."""
    try:
        cfg = CliConfig(api_key=api_key, api_url=api_url)
        client = ViralClient(config=cfg)
        data = client.get(API.AUTH_ME)
        save_config(cfg)
        console.print(f"[green]Logged in as[/] {data.get('name', '?')} ({data.get('email', '?')})")
        console.print(f"  Plan: [cyan]{data.get('plan', '?')}[/]")
        console.print(f"  Config saved to {get_config_path()}")
    except Exception as e:
        handle_error(e)


@app.command()
def register(
    name: str = typer.Option(..., prompt=True),
    email: str = typer.Option(..., prompt=True),
    company: str = typer.Option(None),
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url"),
) -> None:
    """Register a new account (7-day free trial)."""
    try:
        import httpx

        resp = httpx.post(
            f"{api_url}{API.AUTH_REGISTER}",
            json={"name": name, "email": email, "company": company},
            timeout=30.0,
        )
        if resp.status_code >= 400:
            detail = resp.json().get("detail", resp.text)
            console.print(f"[red]Registration failed:[/] {detail}")
            raise typer.Exit(1)

        data = resp.json()
        cfg = CliConfig(api_key=data["api_key"], api_url=api_url)
        save_config(cfg)
        console.print(f"[green]Account created![/] Welcome, {data.get('name', name)}.")
        console.print(f"  Plan: [cyan]{data.get('plan', 'trial')}[/] (7-day trial)")
        console.print(f"  API key: [dim]{data['api_key'][:20]}...[/]")
        console.print(f"  Config saved to {get_config_path()}")
    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command()
def me(
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Show current user info (whoami)."""
    try:
        client = ViralClient()
        data = client.get(API.AUTH_ME)
        fields = [
            ("name", "Name"),
            ("email", "Email"),
            ("company", "Company"),
            ("plan", "Plan"),
            ("calls_used", "API Calls Used"),
            ("calls_limit", "API Calls Limit"),
            ("status", "Status"),
        ]
        render(data, fmt, columns=fields, title="Current User")
    except Exception as e:
        handle_error(e)


@app.command()
def logout() -> None:
    """Remove stored credentials."""
    clear_config()
    console.print("[yellow]Logged out.[/] Credentials removed.")


@app.command()
def config(
    api_url: str = typer.Option(None, help="Set API base URL"),
    default_format: str = typer.Option(None, help="Set default output format (table/json/csv)"),
    show: bool = typer.Option(False, "--show", help="Display current config"),
) -> None:
    """View or update CLI configuration."""
    cfg = load_config()
    if show:
        console.print(f"  Config file: {get_config_path()}")
        console.print(f"  API URL:     {cfg.api_url}")
        key_display = f"{cfg.api_key[:16]}..." if cfg.api_key else "(not set)"
        console.print(f"  API Key:     {key_display}")
        console.print(f"  Format:      {cfg.default_format}")
        return
    changed = False
    if api_url:
        cfg.api_url = api_url
        changed = True
    if default_format:
        cfg.default_format = default_format
        changed = True
    if changed:
        save_config(cfg)
        console.print("[green]Config updated.[/]")
    else:
        console.print("No changes. Use --show to view or pass --api-url / --default-format.")
