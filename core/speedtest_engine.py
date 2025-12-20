from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, Any, Dict

import speedtest

from .units import SpeedResult

StatusCallback = Callable[[str, Dict[str, Any]], None]


@dataclass
class SpeedtestStage:
    name: str
    detail: str | None = None


class SpeedtestEngine:
    """Async wrapper around speedtest-cli with live progress callbacks."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    async def run(self, callback: StatusCallback) -> SpeedResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._run_blocking, callback)

    def _run_blocking(self, callback: StatusCallback) -> SpeedResult:
        self._cancelled = False
        def emit(status: str, **kwargs: Any) -> None:
            callback(status, kwargs)

        emit("finding_server")
        st = speedtest.Speedtest()
        st.get_servers()
        best = st.get_best_server()

        if self._cancelled:
            raise asyncio.CancelledError()

        emit("pinging", server=best)
        st.results.ping

        if self._cancelled:
            raise asyncio.CancelledError()

        download_speeds: list[float] = []
        upload_speeds: list[float] = []

        def download_callback(bytes_recv: float, download_bytes: float, elapsed: float, *_: Any) -> None:
            if elapsed <= 0:
                return
            mbps = (bytes_recv * 8) / 1_000_000 / elapsed
            download_speeds.append(mbps)
            emit("downloading", mbps=mbps)

        def upload_callback(bytes_sent: float, upload_bytes: float, elapsed: float, *_: Any) -> None:
            if elapsed <= 0:
                return
            mbps = (bytes_sent * 8) / 1_000_000 / elapsed
            upload_speeds.append(mbps)
            emit("uploading", mbps=mbps)

        emit("downloading", mbps=0.0)
        st.download(callback=download_callback)
        if self._cancelled:
            raise asyncio.CancelledError()

        emit("uploading", mbps=0.0)
        st.upload(callback=upload_callback, pre_allocate=False)
        if self._cancelled:
            raise asyncio.CancelledError()

        emit("finalizing")
        results = st.results.dict()

        ping_ms = results.get("ping", 0.0)
        jitter_ms = results.get("jitter")
        download_mbps = results.get("download", 0.0) / 1_000_000
        upload_mbps = results.get("upload", 0.0) / 1_000_000
        packet_loss = results.get("packetLoss")
        server = results.get("server", {})
        server_name = None
        if server:
            location = ", ".join(filter(None, [server.get("name"), server.get("country")]))
            server_name = f"{server.get('sponsor', '')} ({location})".strip()
        isp = results.get("client", {}).get("isp")

        # Fallback to observed medians if primary values are zero
        if download_mbps <= 0 and download_speeds:
            download_mbps = max(download_speeds)
        if upload_mbps <= 0 and upload_speeds:
            upload_mbps = max(upload_speeds)

        return SpeedResult(
            ping_ms=ping_ms,
            jitter_ms=jitter_ms,
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            packet_loss=packet_loss,
            server_name=server_name,
            isp=isp,
            timestamp=datetime.utcnow(),
        )
