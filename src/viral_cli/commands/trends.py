"""Trends commands: get."""
import typer
from rich.console import Console

from viral_cli.client import ViralClient
from viral_cli.constants import API
from viral_cli.errors import handle_error
from viral_cli.output import OutputFormat, render

app = typer.Typer(no_args_is_help=True)
console = Console()

HASHTAG_COLUMNS = [
    ("hashtag", "Hashtag"),
    ("count", "Count"),
    ("avg_views", "Avg Views"),
    ("avg_engagement", "Avg Engagement"),
]


@app.command("get")
def get_trends(
    platform: str = typer.Argument(..., help="Platform (tiktok, youtube, instagram, ...)"),
    days: int = typer.Option(30, "--days", "-d", help="Period in days (1-365)"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Get trending hashtags and metrics for a platform."""
    try:
        client = ViralClient()
        data = client.get(f"{API.TRENDS}/{platform}", params={"days": days})

        if fmt == OutputFormat.json:
            render(data, fmt)
            return

        console.print(f"\n[bold]Trends for {data.get('platform', platform)}[/] ({data.get('period', f'{days}d')})")
        console.print(f"  Total content: {data.get('total_content', 0)}")
        console.print(f"  Avg viral score: {data.get('avg_viral_score', 'N/A')}\n")

        hashtags = data.get("top_hashtags", [])
        if hashtags:
            render(hashtags, fmt, columns=HASHTAG_COLUMNS, title="Top Hashtags")
        else:
            console.print("[dim]No hashtag data available.[/]")
    except Exception as e:
        handle_error(e)
