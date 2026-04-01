"""
Format API response data for terminal output.

Three modes:
  - table: Rich Table (default, human-readable)
  - json:  Syntax-highlighted JSON (Rich)
  - csv:   Plain CSV to stdout (pipe-friendly)
"""
import csv
import io
import json
import sys
from enum import Enum
from typing import Any, Sequence

from rich.console import Console
from rich.json import JSON
from rich.table import Table

console = Console()


class OutputFormat(str, Enum):
    table = "table"
    json = "json"
    csv = "csv"


def print_table(
    data: Sequence[dict],
    columns: list[tuple[str, str]],
    title: str | None = None,
) -> None:
    """Render a list of dicts as a Rich table."""
    table = Table(title=title, show_lines=False, pad_edge=True)
    for _, header in columns:
        table.add_column(header)
    for row in data:
        table.add_row(*[str(row.get(k, "")) for k, _ in columns])
    console.print(table)


def print_json(data: Any) -> None:
    """Render JSON — highlighted if terminal, raw if piped."""
    encoded = json.dumps(data, default=str, ensure_ascii=False, indent=2)
    if sys.stdout.isatty():
        console.print(JSON(encoded))
    else:
        print(encoded)


def print_csv(
    data: Sequence[dict], columns: list[tuple[str, str]]
) -> None:
    """Write CSV to stdout (no Rich formatting — pipe-safe)."""
    writer = csv.writer(sys.stdout)
    writer.writerow([header for _, header in columns])
    for row in data:
        writer.writerow([row.get(k, "") for k, _ in columns])


def print_single(data: dict, fields: list[tuple[str, str]]) -> None:
    """Print a single record as key-value pairs."""
    table = Table(show_header=False, box=None, pad_edge=True)
    table.add_column("Field", style="bold cyan", width=22)
    table.add_column("Value")
    for key, label in fields:
        val = data.get(key, "")
        table.add_row(label, str(val))
    console.print(table)


def render(
    data: Any,
    fmt: OutputFormat,
    columns: list[tuple[str, str]] | None = None,
    title: str | None = None,
) -> None:
    """Universal render dispatch."""
    if fmt == OutputFormat.json:
        print_json(data)
    elif fmt == OutputFormat.csv:
        if isinstance(data, list) and columns:
            print_csv(data, columns)
        else:
            for item in data if isinstance(data, list) else [data]:
                print(json.dumps(item, default=str, ensure_ascii=False))
    else:
        if isinstance(data, list) and columns:
            print_table(data, columns, title=title)
        elif isinstance(data, dict) and columns:
            print_single(data, columns)
        else:
            print_json(data)
