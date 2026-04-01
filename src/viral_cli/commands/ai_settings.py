"""AI Settings commands: get, set, usage, models."""
import typer
from rich.console import Console

from viral_cli.client import ViralClient
from viral_cli.constants import API
from viral_cli.errors import handle_error
from viral_cli.output import OutputFormat, print_json, render

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("get")
def get_settings(
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Show current AI model preferences and available models."""
    try:
        client = ViralClient()
        data = client.get(API.AI_SETTINGS)

        if fmt == OutputFormat.json:
            print_json(data)
            return

        prefs = data.get("preferences", data)
        fields = [
            ("sentiment_model", "Sentiment Model"),
            ("ideas_model", "Ideas Model"),
            ("agent_model", "Agent Model"),
        ]
        render(prefs, fmt, columns=fields, title="AI Model Preferences")

        available = data.get("available_models", [])
        if available:
            console.print()
            model_cols = [("key", "Model Key"), ("tier", "Tier"), ("provider", "Provider")]
            render(available, fmt, columns=model_cols, title="Available Models")
    except Exception as e:
        handle_error(e)


@app.command("set")
def set_model(
    sentiment_model: str = typer.Option(None, "--sentiment", help="Model for sentiment analysis"),
    ideas_model: str = typer.Option(None, "--ideas", help="Model for idea generation"),
    agent_model: str = typer.Option(None, "--agent", help="Model for agent tasks"),
) -> None:
    """Update AI model preferences."""
    try:
        client = ViralClient()
        body: dict = {}
        if sentiment_model:
            body["sentiment_model"] = sentiment_model
        if ideas_model:
            body["ideas_model"] = ideas_model
        if agent_model:
            body["agent_model"] = agent_model

        if not body:
            console.print("[yellow]No changes.[/] Use --sentiment, --ideas, or --agent.")
            return

        client.post(API.AI_SETTINGS, json_body=body)
        console.print("[green]AI settings updated.[/]")
        for k, v in body.items():
            console.print(f"  {k}: {v}")
    except Exception as e:
        handle_error(e)


@app.command("usage")
def ai_usage(
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Show AI usage stats for current billing period."""
    try:
        client = ViralClient()
        data = client.get(API.AI_SETTINGS_USAGE)

        if fmt == OutputFormat.json:
            print_json(data)
            return

        items = data.get("usage", data)
        if isinstance(items, list):
            cols = [
                ("model_key", "Model"), ("provider", "Provider"),
                ("call_count", "Calls"), ("total_input_tokens", "Input Tokens"),
                ("total_output_tokens", "Output Tokens"),
                ("estimated_cost_usd", "Cost (USD)"),
            ]
            render(items, fmt, columns=cols, title="AI Usage (Current Period)")
        elif isinstance(items, dict):
            render(items, fmt)
    except Exception as e:
        handle_error(e)


@app.command("models")
def list_models(
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """List all available AI models with tier and cost info."""
    try:
        client = ViralClient()
        data = client.get(API.AI_SETTINGS_MODELS)

        if fmt == OutputFormat.json:
            print_json(data)
            return

        items = data.get("models", data) if isinstance(data, dict) else data
        if isinstance(items, list):
            cols = [
                ("key", "Model"), ("provider", "Provider"), ("tier", "Tier"),
                ("cost_input", "Input $/1M"), ("cost_output", "Output $/1M"),
                ("context_window", "Context"),
            ]
            render(items, fmt, columns=cols, title="Available AI Models")
        else:
            print_json(data)
    except Exception as e:
        handle_error(e)
