"""Billing commands: usage."""
import typer
from rich.console import Console

from viral_cli.client import ViralClient
from viral_cli.constants import API
from viral_cli.errors import handle_error
from viral_cli.output import OutputFormat, print_json

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("usage")
def billing_usage(
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Show current plan usage (API calls, executions, overage)."""
    try:
        client = ViralClient()
        data = client.get(API.BILLING_USAGE)

        if fmt == OutputFormat.json:
            print_json(data)
            return

        plan = data.get("plan_name", "unknown").upper()
        status = data.get("status", "unknown")
        console.print(f"\n[bold]Plan:[/] {plan}  [bold]Status:[/] {status}")
        if data.get("expires_at"):
            console.print(f"  Expires: {data['expires_at']}")

        # API calls bar
        used = data.get("calls_used", 0)
        limit = data.get("calls_limit", 1)
        pct = data.get("pct_used", 0)
        color = "green" if pct < 75 else "yellow" if pct < 90 else "red"
        bar_filled = int(pct / 5)
        bar_empty = 20 - bar_filled
        console.print(f"\n  [bold]API Calls:[/] {used}/{limit} ({pct}%)")
        console.print(f"  [{'=' * bar_filled}{'.' * bar_empty}] [{color}]{pct}%[/]")

        # Executions
        e_used = data.get("executions_used", 0)
        e_limit = data.get("executions_limit", 0)
        e_pct = data.get("executions_pct", 0)
        if e_limit > 0:
            console.print(f"\n  [bold]Executions:[/] {e_used}/{e_limit} ({e_pct}%)")

        # Overage
        overage = data.get("overage_total_brl", 0)
        if overage > 0:
            console.print(f"\n  [bold yellow]Overage:[/] R${overage:.2f}")
            for d in data.get("overage_details", []):
                console.print(
                    f"    {d['type']}: {d['count']}x @ R${d['unit_price_brl']:.2f}"
                    f" = R${d['total_brl']:.2f}"
                )
    except Exception as e:
        handle_error(e)
