from __future__ import annotations

from rich.table import Table

from core.units import SpeedResult


def summarize_quality(result: SpeedResult) -> str:
    if result.download_mbps >= 500 and result.upload_mbps >= 100 and (result.ping_ms or 0) < 20:
        return "ULTRA"
    if result.download_mbps >= 200 and result.upload_mbps >= 50 and (result.ping_ms or 0) < 40:
        return "FAST"
    if result.download_mbps >= 50 and result.upload_mbps >= 10 and (result.ping_ms or 0) < 60:
        return "GOOD"
    return "BASIC"


def render_summary_table(result: SpeedResult) -> Table:
    table = Table(title="Signal Analysis", border_style="#22d3ee")
    table.add_column("Metric", style="#a855f7")
    table.add_column("Verdict", style="#39ff14")
    quality = summarize_quality(result)
    table.add_row("Profile", quality)
    table.add_row("Throughput", f"{result.download_mbps:.1f}↓ / {result.upload_mbps:.1f}↑ Mbps")
    table.add_row("Latency", f"{result.ping_ms:.0f} ms")
    return table
