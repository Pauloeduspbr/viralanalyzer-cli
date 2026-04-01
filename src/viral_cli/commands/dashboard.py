"""Dashboard commands: stats, tui."""
import typer
from rich.console import Console

from viral_cli.client import ViralClient
from viral_cli.constants import API
from viral_cli.errors import handle_error
from viral_cli.output import OutputFormat, print_json, render

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("tui")
def dashboard_tui(
    days: int = typer.Option(30, "--days", "-d", help="Period in days"),
    refresh: int = typer.Option(60, "--refresh", "-r", help="Auto-refresh interval in seconds"),
    web: bool = typer.Option(False, "--web", help="Serve as web app (browser access)"),
    port: int = typer.Option(8180, "--port", "-p", help="Port for web mode"),
    host: str = typer.Option("localhost", "--host", help="Host for web mode"),
) -> None:
    """Launch interactive full-screen dashboard (TUI or Web).

    Terminal: viral dashboard tui
    Browser:  viral dashboard tui --web --port 8180

    Keybindings: [r] Refresh  [p] Toggle pipelines  [q] Quit
    """
    cfg = __import__("viral_cli.config", fromlist=["load_config"]).load_config()
    if not cfg.api_key:
        console.print("[red]No API key configured.[/] Run [cyan]viral auth login[/] first.")
        raise typer.Exit(1)

    from viral_cli.tui.dashboard import DashboardApp

    if web:
        try:
            from textual_serve.server import Server

            console.print(f"[bold green]ViralAnalyzer Web Dashboard[/]")
            console.print(f"  URL: http://{host}:{port}")
            console.print(f"  Press Ctrl+C to stop.\n")

            server = Server(
                f"python -m viral_cli.tui.dashboard --days {days} --refresh {refresh}",
                host=host,
                port=port,
                title="ViralAnalyzer Dashboard",
            )
            server.serve()
        except ImportError:
            console.print(
                "[red]textual-serve not installed.[/] "
                "Run: [cyan]pip install textual-serve[/]"
            )
            raise typer.Exit(1)
    else:
        app_tui = DashboardApp(days=days, refresh_interval=refresh)
        app_tui.run()


@app.command("stats")
def dashboard_stats(
    days: int = typer.Option(30, "--days", "-d"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Show aggregated dashboard KPIs across all platforms."""
    try:
        client = ViralClient()
        data = client.get(API.DASHBOARD_STATS, params={"days": days})

        if fmt == OutputFormat.json:
            print_json(data)
            return

        g = data.get("global", data)
        console.print(f"\n[bold]Dashboard Stats[/] (last {days} days)\n")

        fields = [
            ("total_content", "Total Content"),
            ("total_profiles", "Total Profiles"),
            ("total_ideas", "Total Ideas"),
            ("total_views", "Total Views"),
            ("total_likes", "Total Likes"),
            ("avg_engagement", "Avg Engagement"),
            ("avg_viral_score", "Avg Viral Score"),
        ]
        render(g, fmt, columns=fields, title="Global KPIs")

        platforms = data.get("platforms", [])
        if platforms:
            plat_cols = [
                ("platform", "Platform"),
                ("content_count", "Content"),
                ("total_views", "Views"),
                ("total_likes", "Likes"),
                ("avg_viral_score", "Viral Score"),
            ]
            render(platforms, fmt, columns=plat_cols, title="By Platform")
    except Exception as e:
        handle_error(e)
