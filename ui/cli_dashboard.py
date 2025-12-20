from __future__ import annotations

import asyncio
import contextlib
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyperclip
from rich.align import Align
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Footer, Static

from core.history import export_history, load_history, save_result
from core.speedtest_engine import SpeedtestEngine
from core.units import (
    SpeedResult,
    format_latency,
    format_packet_loss,
    format_speed_dual,
)
from ui.gauges import AnalyzerBars, SpeedometerGauge


class StatusMessage(Message):
    def __init__(self, status: str, speed: float | None = None):
        self.status = status
        self.speed = speed or 0.0
        super().__init__()


class Dashboard(App):
    CSS = """
    Screen {
        background: #05070a;
        color: #e2e8f0;
    }
    #body {
        padding: 1 2;
    }
    Static {
        border: tall #0ea5e9;
        background: #0b1015;
    }
    #title {
        border: none;
    }
    #results {
        min-height: 14;
    }
    #history {
        min-height: 10;
    }
    """

    BINDINGS = [
        ("enter", "start", "Start"),
        ("escape", "stop", "Stop"),
        ("c", "copy", "Copy"),
        ("j", "export", "Export JSON"),
        ("q", "quit", "Quit"),
    ]

    status_text: reactive[str] = reactive("IDLE")
    current_speed: reactive[float] = reactive(0.0)
    result: reactive[Optional[SpeedResult]] = reactive(None)
    running: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.engine = SpeedtestEngine()
        self.speedometer = SpeedometerGauge(max_speed=1200.0)
        self.analyzer = AnalyzerBars(capacity=50)
        self._task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        title = Static(self._title_panel(), id="title")
        gauge = Static(self._speed_panel(), id="gauge")
        analyzer = Static(self.analyzer.render(), id="analyzer")
        results = Static(self._results_panel(), id="results")
        history = Static(self._history_panel(), id="history")

        with Container(id="body"):
            yield title
            with Horizontal():
                yield gauge
                yield analyzer
            yield results
            yield history
            yield Footer()

    def _title_panel(self) -> RenderableType:
        subtitle = f"STATUS: {self.status_text}"
        return Panel(
            Align.center(
                """
┌────────────────────────────────────────────┐
│ SPEEDOMETER SPEED TEST 🚀  │
└────────────────────────────────────────────┘
                """,
                vertical="middle",
            ),
            subtitle=subtitle,
            subtitle_align="right",
            border_style="#22d3ee",
            style="on #0b1015",
        )

    def _speed_panel(self) -> RenderableType:
        return self.speedometer.render(self.current_speed, self.status_text)

    def _analyzer_panel(self) -> RenderableType:
        return self.analyzer.render()

    def _results_panel(self) -> RenderableType:
        table = Table.grid(padding=(0, 1))
        table.add_column("Metric", style="#22d3ee", justify="right")
        table.add_column("Value", style="#39ff14")

        res = self.result
        if res:
            table.add_row("Ping", format_latency(res.ping_ms))
            table.add_row("Jitter", format_latency(res.jitter_ms))
            table.add_row("Download", format_speed_dual(res.download_mbps))
            table.add_row("Upload", format_speed_dual(res.upload_mbps))
            table.add_row("Packet Loss", format_packet_loss(res.packet_loss))
            table.add_row("Server", res.server_name or "Auto")
            table.add_row("ISP", res.isp or "Detected ISP")
            table.add_row("Timestamp", res.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            for label in ["Ping", "Jitter", "Download", "Upload", "Packet Loss", "Server", "ISP", "Timestamp"]:
                table.add_row(label, "—")

        return Panel(table, title="Results", border_style="#0ea5e9", style="on #0b1015")

    def _history_panel(self) -> RenderableType:
        history = load_history()
        table = Table.grid(expand=True)
        table.add_column("When", style="#a855f7")
        table.add_column("Download", style="#39ff14")
        table.add_column("Upload", style="#22d3ee")
        for entry in reversed(history):
            when = entry.timestamp.strftime("%H:%M:%S")
            table.add_row(when, f"{entry.download_mbps:.1f} Mbps", f"{entry.upload_mbps:.1f} Mbps")
        if not history:
            table.add_row("No history", "—", "—")
        return Panel(table, title="Last 10 Runs", border_style="#a855f7", style="on #0b1015")

    def on_mount(self) -> None:
        self.set_interval(1 / 30, self._tick)

    def _tick(self) -> None:
        self.query_one("#title", Static).update(self._title_panel())
        self.query_one("#gauge", Static).update(self._speed_panel())
        self.query_one("#analyzer", Static).update(self._analyzer_panel())
        self.query_one("#results", Static).update(self._results_panel())
        self.query_one("#history", Static).update(self._history_panel())

    async def _run_test(self) -> None:
        self.running = True
        self.result = None
        self.current_speed = 0.0
        self.status_text = "FINDING SERVER"
        self.engine = SpeedtestEngine()

        def callback(status: str, payload: dict) -> None:
            speed = payload.get("mbps", 0.0)
            self.call_from_thread(self.post_message, StatusMessage(status, speed))

        try:
            result = await self.engine.run(callback)
        except asyncio.CancelledError:
            self.running = False
            self.status_text = "CANCELLED"
            return
        except Exception as exc:  # pragma: no cover
            self.running = False
            self.status_text = "ERROR"
            self.current_speed = 0.0
            self.log(f"Speedtest failed: {exc!r}")
            return

        self.result = result
        self.running = False
        self.status_text = "COMPLETE"
        save_result(result)

    def on_status_message(self, message: StatusMessage) -> None:
        status_map = {
            "finding_server": "FINDING SERVER",
            "pinging": "PINGING",
            "downloading": "DOWNLOADING",
            "uploading": "UPLOADING",
            "finalizing": "FINALIZING",
        }
        self.status_text = status_map.get(message.status, message.status.upper())
        if message.speed is not None:
            self.current_speed = message.speed
            self.analyzer.push(message.speed)

    async def action_start(self) -> None:
        if self.running:
            return
        self._task = asyncio.create_task(self._run_test())

    async def action_stop(self) -> None:
        if not self.running:
            return
        self.engine.cancel()
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self.running = False
        self.status_text = "STOPPED"

    def action_copy(self) -> None:
        if not self.result:
            return
        summary = (
            f"Ping: {format_latency(self.result.ping_ms)} | "
            f"Down: {self.result.download_mbps:.2f} Mbps | "
            f"Up: {self.result.upload_mbps:.2f} Mbps"
        )
        try:
            pyperclip.copy(summary)
            self.notify("Copied to clipboard.", severity="information")
        except pyperclip.PyperclipException:
            self.notify("Clipboard unavailable.", severity="warning")

    def action_export(self) -> None:
        path = Path.cwd() / f"speedtest-history-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
        export_history(path)
        self.notify(f"Exported to {path.name}", severity="information")

    async def action_quit(self) -> None:  # type: ignore[override]
        if self.running:
            await self.action_stop()
        await self.shutdown()


def run_dashboard() -> None:
    Dashboard().run()
