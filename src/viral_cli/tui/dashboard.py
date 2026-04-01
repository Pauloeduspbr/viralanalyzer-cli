"""
ViralAnalyzer TUI Dashboard — Interactive terminal dashboard.

Shows real-time KPIs, platform breakdown, pipeline status, and usage
in a full-screen terminal UI with auto-refresh.

Keybindings:
  r — Refresh data now
  p — Toggle pipeline runs panel
  q — Quit

Can be run directly:
  python -m viral_cli.tui.dashboard [--days 7] [--refresh 30]
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

from rich.text import Text
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import DataTable, Footer, Header, Label, Static

from viral_cli.client import ViralClient
from viral_cli.config import load_config
from viral_cli.constants import API


class KpiCard(Static):
    """A single KPI metric card."""

    def __init__(self, title: str, value: str = "—", **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._value = value

    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="kpi-title")
        yield Label(self._value, id=f"kpi-val-{self.id}", classes="kpi-value")

    def update_value(self, value: str) -> None:
        self._value = value
        try:
            label = self.query_one(f"#kpi-val-{self.id}", Label)
            label.update(value)
        except Exception:
            pass


class UsageBar(Static):
    """Usage progress bar with percentage."""

    def __init__(self, label: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._label = label
        self._pct = 0.0
        self._used = 0
        self._limit = 0

    def compose(self) -> ComposeResult:
        yield Label(f"{self._label}: 0/0 (0%)", id=f"usage-{self.id}", classes="usage-label")

    def update_usage(self, used: int, limit: int, pct: float) -> None:
        self._used = used
        self._limit = limit
        self._pct = pct
        color = "green" if pct < 75 else "yellow" if pct < 90 else "red"
        bar_w = 20
        filled = int(pct / 100 * bar_w)
        bar = "█" * filled + "░" * (bar_w - filled)
        text = f"{self._label}: {used:,}/{limit:,} ({pct:.1f}%)  [{color}]{bar}[/]"
        try:
            self.query_one(f"#usage-{self.id}", Label).update(text)
        except Exception:
            pass


class DashboardApp(App):
    """Full-screen ViralAnalyzer dashboard."""

    TITLE = "ViralAnalyzer Dashboard"
    CSS = """
    Screen {
        layout: vertical;
    }
    #kpi-row {
        layout: horizontal;
        height: 5;
        margin: 1 2;
    }
    .kpi-card {
        width: 1fr;
        height: 5;
        border: solid $accent;
        padding: 0 1;
        margin: 0 1;
    }
    .kpi-title {
        text-style: bold;
        color: $text-muted;
    }
    .kpi-value {
        text-style: bold;
        color: $success;
        text-align: center;
    }
    #usage-section {
        height: 4;
        margin: 0 3;
    }
    .usage-label {
        margin: 0 1;
    }
    #platforms-table {
        height: 1fr;
        margin: 1 2;
        border: solid $primary;
    }
    #pipeline-table {
        height: auto;
        max-height: 12;
        margin: 1 2;
        border: solid $warning;
    }
    #status-bar {
        dock: bottom;
        height: 1;
        margin: 0 2;
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("r", "refresh_data", "Refresh"),
        Binding("p", "toggle_pipelines", "Pipelines"),
        Binding("q", "quit", "Quit"),
    ]

    last_refresh: reactive[str] = reactive("never")
    show_pipelines: reactive[bool] = reactive(True)

    def __init__(self, days: int = 30, refresh_interval: int = 60) -> None:
        super().__init__()
        self._days = days
        self._refresh_interval = refresh_interval
        self._client: ViralClient | None = None
        self._timer: Timer | None = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="kpi-row"):
            yield KpiCard("Content", id="kpi-content", classes="kpi-card")
            yield KpiCard("Views", id="kpi-views", classes="kpi-card")
            yield KpiCard("Likes", id="kpi-likes", classes="kpi-card")
            yield KpiCard("Viral Score", id="kpi-viral", classes="kpi-card")
            yield KpiCard("Ideas", id="kpi-ideas", classes="kpi-card")
            yield KpiCard("Profiles", id="kpi-profiles", classes="kpi-card")

        with Container(id="usage-section"):
            yield UsageBar("API Calls", id="usage-api")
            yield UsageBar("Executions", id="usage-exec")

        yield DataTable(id="platforms-table")
        yield DataTable(id="pipeline-table")

        yield Label("Loading...", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize client and start auto-refresh."""
        try:
            self._client = ViralClient(config=load_config())
        except Exception as e:
            self.query_one("#status-bar", Label).update(f"Auth error: {e}")
            return

        # Setup platforms table
        pt = self.query_one("#platforms-table", DataTable)
        pt.add_columns("Platform", "Content", "Views", "Likes", "Viral Score")

        # Setup pipeline table
        pp = self.query_one("#pipeline-table", DataTable)
        pp.add_columns("Pipeline", "Platform", "Status", "Items", "Duration")

        self.load_data()
        self._timer = self.set_interval(self._refresh_interval, self.load_data)

    @work(thread=True)
    def load_data(self) -> None:
        """Fetch all dashboard data in background thread."""
        if not self._client:
            return

        try:
            stats = self._client.get(API.DASHBOARD_STATS, params={"days": self._days})
            usage = self._client.get(API.BILLING_USAGE)
            runs = self._client.get(API.PIPELINE_RUNS, params={"limit": 10})

            self.call_from_thread(self._update_kpis, stats)
            self.call_from_thread(self._update_usage, usage)
            self.call_from_thread(self._update_platforms, stats)
            self.call_from_thread(self._update_pipelines, runs)

            now = datetime.now().strftime("%H:%M:%S")
            self.call_from_thread(
                self.query_one("#status-bar", Label).update,
                f"Last refresh: {now} | Period: {self._days}d | Press [r] to refresh, [q] to quit",
            )
        except Exception as e:
            self.call_from_thread(
                self.query_one("#status-bar", Label).update,
                f"Error: {e}",
            )

    def _update_kpis(self, stats: dict) -> None:
        g = stats.get("global", stats)

        def _fmt(n: int | float | None) -> str:
            if n is None:
                return "—"
            if isinstance(n, float):
                return f"{n:.2f}"
            if n >= 1_000_000_000:
                return f"{n / 1_000_000_000:.1f}B"
            if n >= 1_000_000:
                return f"{n / 1_000_000:.1f}M"
            if n >= 1_000:
                return f"{n / 1_000:.1f}K"
            return str(n)

        self.query_one("#kpi-content", KpiCard).update_value(_fmt(g.get("total_content")))
        self.query_one("#kpi-views", KpiCard).update_value(_fmt(g.get("total_views")))
        self.query_one("#kpi-likes", KpiCard).update_value(_fmt(g.get("total_likes")))
        self.query_one("#kpi-viral", KpiCard).update_value(_fmt(g.get("avg_viral_score")))
        self.query_one("#kpi-ideas", KpiCard).update_value(_fmt(g.get("total_ideas")))
        self.query_one("#kpi-profiles", KpiCard).update_value(_fmt(g.get("total_profiles")))

    def _update_usage(self, usage: dict) -> None:
        api_bar = self.query_one("#usage-api", UsageBar)
        api_bar.update_usage(
            usage.get("calls_used", 0),
            usage.get("calls_limit", 1),
            usage.get("pct_used", 0),
        )
        exec_bar = self.query_one("#usage-exec", UsageBar)
        exec_bar.update_usage(
            usage.get("executions_used", 0),
            usage.get("executions_limit", 1),
            usage.get("executions_pct", 0),
        )

    def _update_platforms(self, stats: dict) -> None:
        table = self.query_one("#platforms-table", DataTable)
        table.clear()
        platforms = stats.get("platforms", [])
        for p in platforms:
            plat = str(p.get("platform", "?")).replace("PlatformType.", "")
            content = str(p.get("content_count", 0))
            views = str(p.get("total_views", 0))
            likes = str(p.get("total_likes", 0))
            viral = f"{p.get('avg_viral_score', 0):.1f}" if p.get("avg_viral_score") else "—"
            if int(p.get("content_count", 0)) > 0:
                table.add_row(plat, content, views, likes, viral)

    def _update_pipelines(self, runs: dict) -> None:
        table = self.query_one("#pipeline-table", DataTable)
        table.clear()
        items = runs.get("data", runs) if isinstance(runs, dict) else runs
        if not isinstance(items, list):
            return
        for r in items[:10]:
            name = str(r.get("pipeline_name", "?"))[:25]
            plat = str(r.get("platform", "?")).replace("PlatformType.", "")
            status = str(r.get("status", "?"))
            processed = str(r.get("items_processed", 0))
            duration = f"{r.get('duration_secs', 0):.1f}s" if r.get("duration_secs") else "—"
            table.add_row(name, plat, status, processed, duration)

    def action_refresh_data(self) -> None:
        """Manual refresh."""
        self.query_one("#status-bar", Label).update("Refreshing...")
        self.load_data()

    def action_toggle_pipelines(self) -> None:
        """Toggle pipeline table visibility."""
        table = self.query_one("#pipeline-table", DataTable)
        table.display = not table.display


# ── Allow direct execution for textual-serve ──
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--refresh", type=int, default=60)
    args = parser.parse_args()

    app = DashboardApp(days=args.days, refresh_interval=args.refresh)
    app.run()
