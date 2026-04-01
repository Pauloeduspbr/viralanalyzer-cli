"""Content commands: list, get."""
import typer

from viral_cli.client import ViralClient
from viral_cli.constants import API
from viral_cli.errors import handle_error
from viral_cli.output import OutputFormat, render

app = typer.Typer(no_args_is_help=True)

COLUMNS = [
    ("id", "ID"),
    ("platform", "Platform"),
    ("profile_username", "Profile"),
    ("content_type", "Type"),
    ("title", "Title"),
]

COLUMNS_METRICS = COLUMNS + [
    ("views", "Views"),
    ("likes", "Likes"),
    ("viral_score", "Viral"),
]


def _flatten(item: dict) -> dict:
    """Flatten nested metrics/analysis into top-level keys."""
    flat = dict(item)
    m = item.get("metrics") or {}
    flat["views"] = m.get("views", 0)
    flat["likes"] = m.get("likes", 0)
    flat["engagement_rate"] = m.get("engagement_rate", "")
    a = item.get("analysis") or {}
    flat["viral_score"] = a.get("viral_score", "")
    return flat


@app.command("list")
def list_content(
    platform: str = typer.Option(None, "--platform", "-p", help="Filter by platform"),
    content_type: str = typer.Option(None, "--type", "-t"),
    min_views: int = typer.Option(None, "--min-views"),
    min_viral_score: int = typer.Option(None, "--min-viral"),
    limit: int = typer.Option(50, "--limit", "-n"),
    offset: int = typer.Option(0, "--offset"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """List collected content with filters."""
    try:
        client = ViralClient()
        params: dict = {"limit": limit, "offset": offset}
        if platform:
            params["platform"] = platform
        if content_type:
            params["content_type"] = content_type
        if min_views is not None:
            params["min_views"] = min_views
        if min_viral_score is not None:
            params["min_viral_score"] = min_viral_score

        resp = client.get(API.CONTENT, params=params)
        items = [_flatten(i) for i in resp.get("data", [])]
        total = resp.get("total", len(items))

        if fmt == OutputFormat.json:
            render(resp, fmt)
        else:
            render(items, fmt, columns=COLUMNS_METRICS, title=f"Content ({total} total)")
    except Exception as e:
        handle_error(e)


@app.command("get")
def get_content(
    content_id: int = typer.Argument(..., help="Content item ID"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Get detailed content with metrics and AI analysis."""
    try:
        client = ViralClient()
        data = client.get(f"{API.CONTENT}/{content_id}")
        flat = _flatten(data)
        fields = [
            ("id", "ID"),
            ("platform", "Platform"),
            ("profile_username", "Profile"),
            ("content_type", "Type"),
            ("title", "Title"),
            ("url", "URL"),
            ("published_at", "Published"),
            ("views", "Views"),
            ("likes", "Likes"),
            ("engagement_rate", "Engagement Rate"),
            ("viral_score", "Viral Score"),
        ]
        render(flat if fmt == OutputFormat.table else data, fmt, columns=fields, title="Content Detail")
    except Exception as e:
        handle_error(e)
