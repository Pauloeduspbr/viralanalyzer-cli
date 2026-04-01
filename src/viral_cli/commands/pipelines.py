"""Pipeline commands: trigger, runs, cancel, quarantine, configs."""
import typer
from rich.console import Console

from viral_cli.client import ViralClient
from viral_cli.constants import API
from viral_cli.errors import handle_error
from viral_cli.output import OutputFormat, print_json, render

app = typer.Typer(no_args_is_help=True)
console = Console()

RUN_COLUMNS = [
    ("id", "ID"),
    ("pipeline_name", "Pipeline"),
    ("platform", "Platform"),
    ("status", "Status"),
    ("items_input", "Input"),
    ("items_processed", "Processed"),
    ("items_failed", "Failed"),
    ("duration_secs", "Duration(s)"),
]

CONFIG_COLUMNS = [
    ("platform", "Platform"),
    ("is_enabled", "Enabled"),
    ("max_results", "Max Results"),
    ("runs_this_month", "Runs/Month"),
    ("last_run_at", "Last Run"),
]


@app.command("trigger")
def trigger_pipeline(
    platform: str = typer.Argument(
        ..., help="Platform to scrape (tiktok, youtube, instagram, ... or 'all')"
    ),
    sentiment_model: str = typer.Option(None, "--sentiment-model", help="Override sentiment AI model"),
    ideas_model: str = typer.Option(None, "--ideas-model", help="Override ideas AI model"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Trigger a scraping pipeline for one or all platforms."""
    try:
        client = ViralClient()
        body: dict = {"platform": platform}
        if sentiment_model:
            body["sentiment_model"] = sentiment_model
        if ideas_model:
            body["ideas_model"] = ideas_model

        with console.status(f"[bold green]Triggering pipeline for {platform}..."):
            resp = client.post(API.PIPELINE_TRIGGER, json_body=body)

        if fmt == OutputFormat.json:
            print_json(resp)
        else:
            if isinstance(resp, dict):
                run_id = resp.get("run_id") or resp.get("id", "?")
                status = resp.get("status", "triggered")
                console.print(f"[green]Pipeline triggered![/] run_id={run_id} status={status}")
                if resp.get("runs"):
                    render(resp["runs"], fmt, columns=RUN_COLUMNS, title="Triggered Runs")
            else:
                console.print(f"[green]Pipeline triggered for {platform}[/]")
    except Exception as e:
        handle_error(e)


@app.command("runs")
def list_runs(
    platform: str = typer.Option(None, "--platform", "-p", help="Filter by platform"),
    status: str = typer.Option(None, "--status", "-s", help="Filter by status (running/completed/failed)"),
    limit: int = typer.Option(20, "--limit", "-n"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """List recent pipeline execution history."""
    try:
        client = ViralClient()
        params: dict = {"limit": limit}
        if platform:
            params["platform"] = platform
        if status:
            params["status"] = status

        resp = client.get(API.PIPELINE_RUNS, params=params)
        items = resp.get("data", resp) if isinstance(resp, dict) else resp
        items = items if isinstance(items, list) else [items]

        if fmt == OutputFormat.json:
            print_json(resp)
        else:
            render(items, fmt, columns=RUN_COLUMNS, title="Pipeline Runs")
    except Exception as e:
        handle_error(e)


@app.command("cancel")
def cancel_run(
    run_id: int = typer.Argument(..., help="Pipeline run ID to cancel"),
) -> None:
    """Cancel a running pipeline execution."""
    try:
        client = ViralClient()
        client.patch(f"{API.PIPELINE_RUNS}/{run_id}/cancel", json_body={})
        console.print(f"[yellow]Pipeline run {run_id} cancelled.[/]")
    except Exception as e:
        handle_error(e)


@app.command("quarantine")
def list_quarantine(
    platform: str = typer.Option(None, "--platform", "-p"),
    limit: int = typer.Option(20, "--limit", "-n"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """List quarantined (failed/suspicious) data items."""
    try:
        client = ViralClient()
        params: dict = {"limit": limit}
        if platform:
            params["platform"] = platform

        resp = client.get(f"{API.PIPELINE_RUNS.replace('/runs', '/quarantine')}", params=params)
        items = resp.get("data", resp) if isinstance(resp, dict) else resp
        items = items if isinstance(items, list) else []

        if fmt == OutputFormat.json:
            print_json(resp)
        else:
            q_cols = [
                ("id", "ID"), ("platform", "Platform"), ("reason", "Reason"),
                ("created_at", "Quarantined At"),
            ]
            render(items, fmt, columns=q_cols, title="Quarantined Items")
    except Exception as e:
        handle_error(e)


@app.command("configs")
def list_configs(
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """List all pipeline configurations for your account."""
    try:
        client = ViralClient()
        resp = client.get(API.PIPELINE_CONFIGS)
        items = resp.get("data", resp) if isinstance(resp, dict) else resp
        items = items if isinstance(items, list) else [items]

        if fmt == OutputFormat.json:
            print_json(resp)
        else:
            render(items, fmt, columns=CONFIG_COLUMNS, title="Pipeline Configs")
    except Exception as e:
        handle_error(e)


@app.command("config-get")
def get_config(
    platform: str = typer.Argument(..., help="Platform name"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Get pipeline config for a specific platform."""
    try:
        client = ViralClient()
        data = client.get(f"{API.PIPELINE_CONFIGS}/{platform}")

        if fmt == OutputFormat.json:
            print_json(data)
        else:
            fields = [
                ("platform", "Platform"), ("is_enabled", "Enabled"),
                ("max_results", "Max Results"), ("runs_this_month", "Runs/Month"),
                ("last_run_at", "Last Run"), ("search_params", "Search Params"),
            ]
            render(data, fmt, columns=fields, title=f"Config: {platform}")
    except Exception as e:
        handle_error(e)


@app.command("config-set")
def set_config(
    platform: str = typer.Argument(..., help="Platform name"),
    enabled: bool = typer.Option(None, "--enabled/--disabled", help="Enable or disable"),
    max_results: int = typer.Option(None, "--max-results"),
) -> None:
    """Update pipeline config for a platform."""
    try:
        client = ViralClient()
        body: dict = {}
        if enabled is not None:
            body["is_enabled"] = enabled
        if max_results is not None:
            body["max_results"] = max_results

        if not body:
            console.print("[yellow]No changes specified.[/] Use --enabled/--disabled or --max-results.")
            return

        client.patch(f"{API.PIPELINE_CONFIGS}/{platform}", json_body=body)
        console.print(f"[green]Config updated for {platform}[/]")
    except Exception as e:
        handle_error(e)


@app.command("limits")
def plan_limits(
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Show pipeline execution limits for your plan."""
    try:
        client = ViralClient()
        data = client.get(f"{API.PIPELINE_CONFIGS}/plan-limits")

        if fmt == OutputFormat.json:
            print_json(data)
        else:
            fields = [
                ("max_platforms", "Max Platforms"),
                ("max_targets_per_platform", "Max Targets/Platform"),
                ("max_results_per_target", "Max Results/Target"),
                ("max_executions_per_month", "Max Executions/Month"),
                ("max_ideas_per_month", "Max Ideas/Month"),
            ]
            render(data, fmt, columns=fields, title="Plan Limits")
    except Exception as e:
        handle_error(e)
