"""Engagement commands: stats, actions, ai-reply."""
import typer
from rich.console import Console

from viral_cli.client import ViralClient
from viral_cli.errors import handle_error
from viral_cli.output import OutputFormat, print_json, render

app = typer.Typer(no_args_is_help=True)
console = Console()

ENGAGE_API = "/api/v1/engage"


@app.command("stats")
def engage_stats(
    days: int = typer.Option(7, "--days", "-d", help="Period in days"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Show engagement automation stats."""
    try:
        client = ViralClient()
        data = client.get(f"{ENGAGE_API}/stats", params={"days": days})

        if fmt == OutputFormat.json:
            print_json(data)
            return

        console.print(f"\n[bold]Engagement Stats[/] (last {days} days)\n")
        console.print(f"  Total actions: [bold]{data.get('total_actions', 0)}[/]")
        console.print(f"  Today: {data.get('actions_today', 0)}")
        console.print(f"  Last hour: {data.get('actions_last_hour', 0)}")

        by_platform = data.get("by_platform", {})
        if by_platform:
            console.print("\n  [bold]By Platform:[/]")
            for plat, count in sorted(by_platform.items(), key=lambda x: -x[1]):
                console.print(f"    {plat:15} {count}")

        by_type = data.get("by_action_type", {})
        if by_type:
            console.print("\n  [bold]By Action Type:[/]")
            for atype, count in sorted(by_type.items(), key=lambda x: -x[1]):
                console.print(f"    {atype:15} {count}")

        by_agent = data.get("by_agent", {})
        if by_agent:
            console.print("\n  [bold]By Agent:[/]")
            for agent, count in sorted(by_agent.items(), key=lambda x: -x[1]):
                console.print(f"    {agent:20} {count}")
    except Exception as e:
        handle_error(e)


@app.command("actions")
def list_actions(
    platform: str = typer.Option(None, "--platform", "-p"),
    action_type: str = typer.Option(None, "--type", "-t", help="reply|like|retweet|quote_tweet"),
    limit: int = typer.Option(20, "--limit", "-n"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """List engagement actions taken (audit log)."""
    try:
        client = ViralClient()
        params: dict = {"limit": limit}
        if platform:
            params["platform"] = platform
        if action_type:
            params["action_type"] = action_type

        resp = client.get(f"{ENGAGE_API}/actions", params=params)
        items = resp.get("data", resp) if isinstance(resp, dict) else resp
        items = items if isinstance(items, list) else []

        if fmt == OutputFormat.json:
            print_json(resp)
        else:
            cols = [
                ("id", "ID"), ("platform", "Platform"), ("action_type", "Action"),
                ("agent_name", "Agent"), ("target_user", "Target"),
                ("created_at", "Timestamp"),
            ]
            render(items, fmt, columns=cols, title="Engagement Actions")
    except Exception as e:
        handle_error(e)


@app.command("ai-reply")
def ai_reply(
    platform: str = typer.Argument(..., help="Platform (twitter, linkedin, instagram)"),
    post_id: str = typer.Argument(..., help="Post/tweet ID to reply to"),
    tone: str = typer.Option("helpful", "--tone", help="Reply tone: helpful|witty|professional|casual"),
    agent: str = typer.Option("comment_responder", "--agent", help="Agent name"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Generate reply without posting"),
) -> None:
    """Generate and post an AI-powered reply."""
    try:
        client = ViralClient()
        body: dict = {
            "platform": platform,
            "post_id": post_id,
            "tone": tone,
            "agent_name": agent,
            "dry_run": dry_run,
        }

        with console.status("[bold green]Generating AI reply..."):
            resp = client.post(f"{ENGAGE_API}/ai-reply", json_body=body)

        if isinstance(resp, dict):
            reply_text = resp.get("reply_text", resp.get("text", ""))
            posted = resp.get("posted", not dry_run)
            console.print(f"\n[bold]AI Reply{'(dry run)' if dry_run else ''}:[/]")
            console.print(f"  {reply_text}")
            if posted:
                console.print(f"\n  [green]Posted to {platform}[/]")
            else:
                console.print(f"\n  [yellow]Not posted (dry run)[/]")
        else:
            print_json(resp)
    except Exception as e:
        handle_error(e)
