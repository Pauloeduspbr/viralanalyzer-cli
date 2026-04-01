"""Ideas commands: list, get, generate, update, performance, summary."""
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
    ("source_platform", "Source"),
    ("target_platform", "Target"),
    ("title", "Title"),
    ("estimated_score", "Score"),
    ("status", "Status"),
]


@app.command("list")
def list_ideas(
    platform: str = typer.Option(None, "--platform", "-p"),
    status: str = typer.Option(
        None, "--status", "-s",
        help="generated|reviewed|in_production|published|discarded",
    ),
    min_score: int = typer.Option(None, "--min-score"),
    limit: int = typer.Option(50, "--limit", "-n"),
    offset: int = typer.Option(0, "--offset"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """List AI-generated content ideas."""
    try:
        client = ViralClient()
        params: dict = {"limit": limit, "offset": offset}
        if platform:
            params["platform"] = platform
        if status:
            params["status"] = status
        if min_score is not None:
            params["min_score"] = min_score

        resp = client.get(API.IDEAS, params=params)
        items = resp.get("data", []) if isinstance(resp, dict) else resp
        total = resp.get("total", len(items)) if isinstance(resp, dict) else len(items)

        if fmt == OutputFormat.json:
            render(resp, fmt)
        else:
            render(items, fmt, columns=COLUMNS, title=f"Ideas ({total} total)")
    except Exception as e:
        handle_error(e)


@app.command("get")
def get_idea(
    idea_id: int = typer.Argument(..., help="Idea ID"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Get a single idea with full details."""
    try:
        client = ViralClient()
        data = client.get(f"{API.IDEAS}/{idea_id}")
        fields = [
            ("id", "ID"), ("title", "Title"), ("hook", "Hook"), ("cta", "CTA"),
            ("source_platform", "Source"), ("target_platform", "Target"),
            ("estimated_score", "Score"), ("viral_potential", "Viral Potential"),
            ("status", "Status"), ("notes", "Notes"),
            ("generated_at", "Generated"), ("published_url", "Published URL"),
        ]
        render(data, fmt, columns=fields, title="Idea Detail")
    except Exception as e:
        handle_error(e)


@app.command("generate")
def generate_ideas(
    count: int = typer.Option(3, "--count", "-n", help="Ideas per platform (1-20)"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Trigger AI idea generation from analyzed content."""
    try:
        client = ViralClient()
        resp = client.post(API.IDEAS_GENERATE, params={"num_ideas": count})
        generated = resp.get("generated", 0) if isinstance(resp, dict) else 0
        console.print(f"[green]Generated {generated} ideas[/]")
        if fmt == OutputFormat.json:
            render(resp, fmt)
    except Exception as e:
        handle_error(e)


@app.command("update")
def update_idea(
    idea_id: int = typer.Argument(..., help="Idea ID"),
    status: str = typer.Option(
        ..., "--status", "-s",
        help="generated|reviewed|in_production|published|discarded",
    ),
    notes: str = typer.Option(None, "--notes"),
    published_url: str = typer.Option(None, "--published-url"),
    discarded_reason: str = typer.Option(None, "--reason"),
    target_platform: str = typer.Option(None, "--target"),
) -> None:
    """Update idea status (lifecycle transition)."""
    try:
        client = ViralClient()
        body: dict = {"status": status}
        if notes:
            body["notes"] = notes
        if published_url:
            body["published_url"] = published_url
        if discarded_reason:
            body["discarded_reason"] = discarded_reason
        if target_platform:
            body["target_platform"] = target_platform

        client.patch(f"{API.IDEAS}/{idea_id}", json_body=body)
        console.print(f"[green]Idea {idea_id} updated to '{status}'[/]")
    except Exception as e:
        handle_error(e)


@app.command("performance")
def update_performance(
    idea_id: int = typer.Argument(...),
    views: int = typer.Option(None),
    likes: int = typer.Option(None),
    comments: int = typer.Option(None),
    shares: int = typer.Option(None),
    engagement: float = typer.Option(None),
) -> None:
    """Update performance metrics for a published idea."""
    try:
        client = ViralClient()
        body: dict = {}
        if views is not None:
            body["views"] = views
        if likes is not None:
            body["likes"] = likes
        if comments is not None:
            body["comments"] = comments
        if shares is not None:
            body["shares"] = shares
        if engagement is not None:
            body["engagement"] = engagement

        client.patch(f"{API.IDEAS}/{idea_id}/performance", json_body=body)
        console.print(f"[green]Performance updated for idea {idea_id}[/]")
    except Exception as e:
        handle_error(e)


@app.command("summary")
def lifecycle_summary(
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Show idea lifecycle summary (counts by status)."""
    try:
        client = ViralClient()
        data = client.get(API.IDEAS_LIFECYCLE)
        if fmt == OutputFormat.json:
            render(data, fmt)
        else:
            by_status = data.get("by_status", {})
            items = [{"status": k, "count": v} for k, v in by_status.items()]
            render(
                items, fmt,
                columns=[("status", "Status"), ("count", "Count")],
                title=f"Idea Lifecycle (total: {data.get('total', 0)})",
            )
    except Exception as e:
        handle_error(e)
