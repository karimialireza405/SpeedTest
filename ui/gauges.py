from __future__ import annotations

import math
import random
from typing import List

from rich.panel import Panel
from rich.text import Text

CYBER_COLORS = ["#2de370", "#28d7e5", "#a855f7", "#ff3864"]


class SpeedometerGauge:
    def __init__(self, max_speed: float = 1000.0) -> None:
        self.max_speed = max_speed

    def render(self, speed_mbps: float, status: str) -> Panel:
        clamped = max(0.0, min(speed_mbps, self.max_speed))
        ratio = clamped / self.max_speed
        angle = ratio * math.pi
        needle_pos = int(ratio * 28)

        tick_line = "".join("▄" if i <= needle_pos else "·" for i in range(29))
        needle = " " * needle_pos + "⚡"

        speed_text = Text(f"{speed_mbps:6.2f} Mbps", style="bold #2de370")
        status_text = Text(status.upper(), style="bold #a855f7")

        lines = [
            Text("┌" + "─" * 29 + "┐", style="#0b1015"),
            Text("│" + tick_line + "│", style="#0b1015"),
            Text("│" + needle.ljust(29) + "│", style="#0b1015"),
            Text("└" + "─" * 29 + "┘", style="#0b1015"),
        ]
        body = Text("\n").join(lines)
        body.append("\n")
        body.append(speed_text)
        body.append("  ")
        body.append(status_text)

        return Panel(
            body,
            border_style="#22d3ee",
            title="SPEEDOMETER 🚀",
            style="on #0b1015",
        )


class AnalyzerBars:
    def __init__(self, capacity: int = 40) -> None:
        self.capacity = capacity
        self.samples: List[float] = []

    def push(self, value: float) -> None:
        self.samples.append(value)
        if len(self.samples) > self.capacity:
            self.samples.pop(0)

    def render(self) -> Panel:
        blocks = "▁▂▃▄▅▆▇█"
        if not self.samples:
            spark = "".join(random.choice(blocks[:2]) for _ in range(self.capacity))
        else:
            max_sample = max(self.samples) or 1
            normalized = [min(int((val / max_sample) * (len(blocks) - 1)), len(blocks) - 1) for val in self.samples]
            spark = "".join(blocks[idx] for idx in normalized)
            spark = spark.rjust(self.capacity, blocks[0])

        text = Text(spark, style="#39ff14")
        return Panel(text, title="Analyzer", border_style="#a855f7", style="on #0b1015")


def cyber_label(text: str, color: str | None = None) -> Text:
    style = color or random.choice(CYBER_COLORS)
    return Text(text, style=f"bold {style}")
