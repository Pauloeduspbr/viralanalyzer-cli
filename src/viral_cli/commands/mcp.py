"""MCP commands: serve, inspect."""
import typer
from rich.console import Console

from viral_cli.config import get_config_path, load_config
from viral_cli.errors import handle_error

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("serve")
def serve(
    transport: str = typer.Option(
        "stdio", "--transport", "-t",
        help="Transport: stdio (Claude Desktop/VS Code) or sse (HTTP)",
    ),
    port: int = typer.Option(3100, "--port", "-p", help="Port for SSE transport"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host for SSE transport"),
) -> None:
    """Start the MCP server (14 tools for AI assistants).

    stdio: For Claude Desktop, VS Code, Cursor — reads from stdin/stdout.
    sse: HTTP server with Server-Sent Events — for network access.
    """
    cfg = load_config()
    if not cfg.api_key:
        console.print(
            "[red]No API key configured.[/] "
            "Run [cyan]viral auth login[/] first."
        )
        raise typer.Exit(1)

    from viral_cli.mcp_proxy import create_mcp_server

    mcp = create_mcp_server()

    console.print(f"[bold green]ViralAnalyzer MCP Server[/]")
    console.print(f"  Transport: {transport}")
    console.print(f"  API URL:   {cfg.api_url}")
    console.print(f"  Config:    {get_config_path()}")
    console.print(f"  Tools:     14")

    if transport == "sse":
        if host != "127.0.0.1" and host != "localhost":
            console.print("[yellow bold]WARNING:[/] SSE mode on non-localhost exposes tools without auth!")
            console.print("  Consider using --host 127.0.0.1 (default) for local-only access.")
        console.print(f"  Endpoint:  http://{host}:{port}/sse")
        console.print(f"\n[dim]Press Ctrl+C to stop.[/]\n")
        mcp.settings.port = port
        mcp.settings.host = host
        mcp.run(transport="sse")
    else:
        console.print(f"\n[dim]Running in stdio mode. Connect from Claude Desktop or VS Code.[/]\n")
        mcp.run(transport="stdio")


@app.command("inspect")
def inspect() -> None:
    """List all available MCP tools and resources."""
    from viral_cli.mcp_proxy import create_mcp_server

    mcp = create_mcp_server()

    console.print("\n[bold]MCP Tools (14):[/]\n")

    # Tools are registered in the FastMCP instance
    tools = mcp._tool_manager._tools if hasattr(mcp, '_tool_manager') else {}
    if not tools:
        # Fallback: list known tools
        tool_list = [
            ("search_content", "Search viral content across 25+ platforms"),
            ("get_content_detail", "Get full details of a content item"),
            ("get_platform_trends", "Get trending hashtags for a platform"),
            ("list_profiles", "List monitored social media profiles"),
            ("add_profile", "Add a new profile to monitor"),
            ("find_businesses", "Search Google Maps business data"),
            ("enrich_cnpj", "Look up Brazilian company data"),
            ("get_competitor_intel", "Get competitor intelligence data"),
            ("get_dashboard_stats", "Get aggregated KPIs"),
            ("list_ideas", "List AI-generated content ideas"),
            ("trigger_pipeline", "Trigger data collection pipeline"),
            ("list_pipeline_runs", "List pipeline execution history"),
            ("get_usage_stats", "Get API usage and subscription status"),
        ]
        for name, desc in tool_list:
            console.print(f"  [cyan]{name:25}[/] {desc}")
    else:
        for name, tool in tools.items():
            desc = (tool.description or "")[:60]
            console.print(f"  [cyan]{name:25}[/] {desc}")

    console.print("\n[bold]Resources (2):[/]\n")
    console.print("  [cyan]viralanalyzer://platforms[/]  List of 25 supported platforms")
    console.print("  [cyan]viralanalyzer://help[/]       Quick start guide")

    console.print("\n[bold]Usage:[/]")
    console.print("  viral mcp serve                    # stdio (Claude Desktop)")
    console.print("  viral mcp serve --transport sse     # SSE HTTP server")
    console.print()
