"""Analyze commands: file, hook (git pre-commit integration)."""
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from viral_cli.client import ViralClient
from viral_cli.errors import handle_error
from viral_cli.output import OutputFormat, print_json

app = typer.Typer(no_args_is_help=True)
console = Console()


def _read_file(path: Path) -> str:
    """Read file content, raise if not found."""
    if not path.exists():
        console.print(f"[red]File not found:[/] {path}")
        raise typer.Exit(1)
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_title(content: str) -> str:
    """Extract title from markdown (first # heading) or first line."""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped and not stripped.startswith("---"):
            return stripped[:100]
    return "Untitled"


@app.command("file")
def analyze_file(
    file_path: Path = typer.Argument(..., help="Path to .md or .txt file to analyze"),
    min_score: float = typer.Option(0, "--min-score", help="Fail if viral score below this (for CI)"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Analyze a local content file for viral potential using AI.

    Sends the content to the ViralAnalyzer API for viral analysis
    (sentiment, hooks, power words, estimated viral score).

    Use --min-score in CI to fail if content doesn't meet threshold.
    """
    try:
        content = _read_file(file_path)
        title = _extract_title(content)

        # Truncate to ~4000 chars to stay within reasonable API limits
        if len(content) > 4000:
            content = content[:4000] + "\n\n[truncated]"

        client = ViralClient()

        with console.status(f"[bold green]Analyzing {file_path.name}..."):
            resp = client.post(
                "/api/v1/content/analyze",
                json_body={
                    "title": title,
                    "description": content,
                    "platform": "blog",
                    "content_type": "blog_article",
                },
            )

        if fmt == OutputFormat.json:
            print_json(resp)
        else:
            analysis = resp.get("analysis", resp)
            viral_score = analysis.get("viral_score", 0)
            sentiment = analysis.get("sentiment", "unknown")
            hooks = analysis.get("hooks", [])
            power_words = analysis.get("power_words", [])
            lessons = analysis.get("lessons", [])

            # Score color
            if viral_score >= 7:
                score_color = "green"
            elif viral_score >= 5:
                score_color = "yellow"
            else:
                score_color = "red"

            console.print(f"\n[bold]Analysis: {file_path.name}[/]")
            console.print(f"  Title: {title}")
            console.print(f"  Viral Score: [{score_color} bold]{viral_score}/10[/]")
            console.print(f"  Sentiment: {sentiment}")

            if hooks:
                console.print(f"\n  [bold]Hooks:[/]")
                for h in hooks[:5]:
                    console.print(f"    - {h}")

            if power_words:
                console.print(f"\n  [bold]Power Words:[/] {', '.join(power_words[:10])}")

            if lessons:
                console.print(f"\n  [bold]Lessons:[/]")
                for l in lessons[:3]:
                    console.print(f"    - {l}")

        # CI gate: fail if score below threshold
        if min_score > 0:
            score = resp.get("analysis", resp).get("viral_score", 0)
            if score < min_score:
                console.print(
                    f"\n[red bold]FAIL:[/] Viral score {score} < {min_score} (min threshold)"
                )
                raise typer.Exit(1)
            else:
                console.print(
                    f"\n[green bold]PASS:[/] Viral score {score} >= {min_score}"
                )

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("dir")
def analyze_dir(
    directory: Path = typer.Argument(".", help="Directory to scan for .md files"),
    min_score: float = typer.Option(0, "--min-score", help="Fail if any file below threshold"),
    glob_pattern: str = typer.Option("**/*.md", "--pattern", "-p", help="File pattern to match"),
    fmt: OutputFormat = typer.Option("table", "--format", "-f"),
) -> None:
    """Analyze all markdown files in a directory.

    Useful for CI: viral analyze dir ./content --min-score 6
    """
    try:
        files = sorted(Path(directory).glob(glob_pattern))
        if not files:
            console.print(f"[yellow]No files matching {glob_pattern} in {directory}[/]")
            return

        console.print(f"[bold]Analyzing {len(files)} files in {directory}[/]\n")

        client = ViralClient()
        results = []
        failed = False

        for fp in files:
            content = fp.read_text(encoding="utf-8", errors="replace")
            title = _extract_title(content)
            if len(content) > 4000:
                content = content[:4000]

            try:
                resp = client.post(
                    "/api/v1/content/analyze",
                    json_body={
                        "title": title,
                        "description": content,
                        "platform": "blog",
                        "content_type": "blog_article",
                    },
                )
                analysis = resp.get("analysis", resp)
                score = analysis.get("viral_score", 0)
                sentiment = analysis.get("sentiment", "?")

                if score >= 7:
                    icon, color = "PASS", "green"
                elif score >= 5:
                    icon, color = "WARN", "yellow"
                else:
                    icon, color = "LOW", "red"

                console.print(
                    f"  [{color}]{icon}[/] {score:4.1f}/10  {sentiment:10}  {fp.name}"
                )
                results.append({"file": str(fp), "score": score, "sentiment": sentiment})

                if min_score > 0 and score < min_score:
                    failed = True

            except Exception as e:
                console.print(f"  [red]ERR[/]  ---/10  error       {fp.name}: {e}")
                results.append({"file": str(fp), "score": 0, "sentiment": "error"})
                if min_score > 0:
                    failed = True

        if fmt == OutputFormat.json:
            print_json(results)

        # Summary
        if results:
            avg = sum(r["score"] for r in results) / len(results)
            console.print(f"\n  Average: {avg:.1f}/10 across {len(results)} files")

        if failed:
            console.print(f"\n[red bold]FAIL:[/] Some files below min score {min_score}")
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        handle_error(e)


@app.command("hook")
def install_hook(
    min_score: float = typer.Option(6, "--min-score", help="Minimum viral score to pass"),
    pattern: str = typer.Option("content/**/*.md", "--pattern", help="Glob pattern for files to analyze"),
) -> None:
    """Install a git pre-commit hook that analyzes content files.

    The hook runs 'viral analyze dir' on staged .md files before commit.
    """
    git_dir = Path(".git")
    if not git_dir.exists():
        console.print("[red]Not a git repository.[/] Run from a repo root.")
        raise typer.Exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_file = hooks_dir / "pre-commit"

    hook_content = f"""#!/bin/sh
# ViralAnalyzer content quality gate
# Installed by: viral analyze hook

# Check if viral CLI is available
if ! command -v viral &> /dev/null; then
    echo "viral CLI not found. Install: pip install -e ./cli"
    exit 0  # Don't block commit if CLI not installed
fi

# Get staged .md files matching pattern
STAGED_MD=$(git diff --cached --name-only --diff-filter=ACM | grep -E '{pattern}')

if [ -n "$STAGED_MD" ]; then
    echo "ViralAnalyzer: Analyzing staged content files..."
    for f in $STAGED_MD; do
        viral analyze file "$f" --min-score {min_score} --format table
        if [ $? -ne 0 ]; then
            echo ""
            echo "Content quality gate FAILED for: $f"
            echo "Improve the content or use --no-verify to skip."
            exit 1
        fi
    done
    echo "ViralAnalyzer: All content passed quality gate."
fi
"""

    hook_file.write_text(hook_content, encoding="utf-8")
    # Make executable (Unix)
    try:
        os.chmod(str(hook_file), 0o755)
    except OSError:
        pass  # Windows doesn't need chmod

    console.print(f"[green]Pre-commit hook installed![/]")
    console.print(f"  File: {hook_file}")
    console.print(f"  Pattern: {pattern}")
    console.print(f"  Min score: {min_score}")
    console.print(f"\n  Staged .md files will be analyzed before each commit.")
    console.print(f"  Skip with: git commit --no-verify")
