from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from ..utils import now_utc


PING_RE = re.compile(r"time[=<]([0-9]+(?:\.[0-9]+)?)")


@dataclass(frozen=True)
class ServerStatus:
    host: str
    port: int
    checked_at: datetime
    ping_ms: float | None
    tcp_latency_ms: float | None
    telegram_latency_ms: float | None
    tcp_available: bool
    auth_available: bool | None
    

async def _measure_ping_ms(host: str, timeout_seconds: int = 2) -> float | None:
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping",
            "-c",
            "1",
            "-W",
@@ -48,143 +43,40 @@ async def _measure_ping_ms(host: str, timeout_seconds: int = 2) -> float | None:

    output = stdout.decode("utf-8", errors="ignore")
    match = PING_RE.search(output)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


async def _measure_tcp_latency_ms(host: str, port: int, timeout_seconds: float = 2.5) -> tuple[bool, float | None]:
    loop = asyncio.get_running_loop()
    started = loop.time()
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout_seconds)
        _ = reader
        latency_ms = (loop.time() - started) * 1000
        writer.close()
        await writer.wait_closed()
        return True, latency_ms
    except Exception:
        return False, None


async def get_server_status(host: str, port: int) -> ServerStatus:
    ping_ms, (tcp_available, tcp_latency_ms) = await asyncio.gather(
        _measure_ping_ms(host),
        _measure_tcp_latency_ms(host, port),
    )
    return ServerStatus(
        host=host,
        port=port,
        checked_at=now_utc(),
        ping_ms=ping_ms,
        tcp_latency_ms=tcp_latency_ms,
        telegram_latency_ms=None,
        tcp_available=tcp_available,
        auth_available=None,
    )
