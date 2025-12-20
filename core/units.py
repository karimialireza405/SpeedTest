from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class SpeedResult:
    ping_ms: float
    jitter_ms: float | None
    download_mbps: float
    upload_mbps: float
    packet_loss: float | None
    server_name: str | None
    isp: str | None
    timestamp: datetime

    @property
    def download_mbs(self) -> float:
        return mbps_to_mbs(self.download_mbps)

    @property
    def upload_mbs(self) -> float:
        return mbps_to_mbs(self.upload_mbps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ping_ms": self.ping_ms,
            "jitter_ms": self.jitter_ms,
            "download_mbps": self.download_mbps,
            "upload_mbps": self.upload_mbps,
            "packet_loss": self.packet_loss,
            "server_name": self.server_name,
            "isp": self.isp,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeedResult":
        return cls(
            ping_ms=data.get("ping_ms", 0.0),
            jitter_ms=data.get("jitter_ms"),
            download_mbps=data.get("download_mbps", 0.0),
            upload_mbps=data.get("upload_mbps", 0.0),
            packet_loss=data.get("packet_loss"),
            server_name=data.get("server_name"),
            isp=data.get("isp"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


def mbps_to_mbs(mbps: float) -> float:
    return mbps / 8.0


def format_speed(mbps: float) -> str:
    return f"{mbps:6.2f} Mbps"


def format_speed_dual(mbps: float) -> str:
    mbs = mbps_to_mbs(mbps)
    return f"{mbps:6.2f} Mbps | {mbs:6.2f} MB/s"


def format_latency(latency_ms: float | None) -> str:
    if latency_ms is None or math.isnan(latency_ms):
        return "N/A"
    return f"{latency_ms:.0f} ms"


def format_packet_loss(loss: float | None) -> str:
    if loss is None or math.isnan(loss):
        return "N/A"
    return f"{loss:.1f}%"
