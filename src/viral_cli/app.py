"""
Root Typer application — registers all command groups.

Usage:
    viral auth login
    viral content list --platform youtube
    viral ideas generate --count 5
    viral dashboard stats
    viral billing usage
"""
import typer

from viral_cli.constants import APP_VERSION

app = typer.Typer(
    name="viral",
    help="ViralAnalyzer CLI — competitive intelligence from your terminal.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _version_callback(value: bool) -> None:
    if value:
        print(f"viral-analyzer-cli {APP_VERSION}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False, "--version", "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """ViralAnalyzer CLI — competitive intelligence from your terminal."""


# Register command groups
from viral_cli.commands import (  # noqa: E402
    ai_settings,
    analyze,
    auth,
    billing,
    content,
    dashboard,
    engage,
    ideas,
    mcp,
    pipelines,
    profiles,
    trends,
)

app.add_typer(auth.app, name="auth", help="Authentication: login, register, whoami")
app.add_typer(content.app, name="content", help="Browse and search collected content")
app.add_typer(ideas.app, name="ideas", help="AI-generated content ideas")
app.add_typer(trends.app, name="trends", help="Platform trend analysis")
app.add_typer(profiles.app, name="profiles", help="Manage monitored profiles")
app.add_typer(pipelines.app, name="pipelines", help="Pipeline execution and configs")
app.add_typer(dashboard.app, name="dashboard", help="Dashboard KPIs and history")
app.add_typer(billing.app, name="billing", help="Plan usage and billing info")
app.add_typer(ai_settings.app, name="ai", help="AI model settings and usage")
app.add_typer(engage.app, name="engage", help="Engagement automation and stats")
app.add_typer(analyze.app, name="analyze", help="Analyze content files for viral potential")
app.add_typer(mcp.app, name="mcp", help="MCP server for AI assistants (Claude, Cursor, VS Code)")


def main() -> None:
    """Entry point for the CLI."""
    app()
