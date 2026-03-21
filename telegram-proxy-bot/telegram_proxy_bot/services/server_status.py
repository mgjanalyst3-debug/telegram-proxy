from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime
from ipaddress import ip_address

from ..models import Subscription
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
            str(timeout_seconds),
            host,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
    except Exception:
        return None

    if proc.returncode != 0:
        return None

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


async def _probe_socks_auth(
    host: str,
    port: int,
    username: str,
    password: str,
    timeout_seconds: float = 3.0,
) -> bool | None:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout_seconds)
    except Exception:
        return None

    try:
        writer.write(b"\x05\x01\x02")
        await writer.drain()
        hello = await asyncio.wait_for(reader.readexactly(2), timeout=timeout_seconds)
        if hello[0] != 0x05:
            return False
        if hello[1] == 0xFF:
            return False
        if hello[1] != 0x02:
            return True

        username_b = username.encode("utf-8", errors="ignore")[:255]
        password_b = password.encode("utf-8", errors="ignore")[:255]
        auth_req = (
            bytes([0x01, len(username_b)])
            + username_b
            + bytes([len(password_b)])
            + password_b
        )
        writer.write(auth_req)
        await writer.drain()
        auth_resp = await asyncio.wait_for(reader.readexactly(2), timeout=timeout_seconds)
        return auth_resp[0] == 0x01 and auth_resp[1] == 0x00
    except Exception:
        return False
    finally:
        writer.close()
        await writer.wait_closed()
async def _measure_telegram_via_socks_latency_ms(
    host: str,
    port: int,
    username: str,
    password: str,
    target_host: str = "149.154.167.51",
    target_port: int = 443,
    timeout_seconds: float = 4.0,
) -> float | None:
    loop = asyncio.get_running_loop()
    started = loop.time()
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout_seconds)
    except Exception:
        return None

    try:
        writer.write(b"\x05\x01\x02")
        await writer.drain()
        hello = await asyncio.wait_for(reader.readexactly(2), timeout=timeout_seconds)
        if hello != b"\x05\x02":
            return None

        username_b = username.encode("utf-8", errors="ignore")[:255]
        password_b = password.encode("utf-8", errors="ignore")[:255]
        auth_req = bytes([0x01, len(username_b)]) + username_b + bytes([len(password_b)]) + password_b
        writer.write(auth_req)
        await writer.drain()
        auth_resp = await asyncio.wait_for(reader.readexactly(2), timeout=timeout_seconds)
        if auth_resp != b"\x01\x00":
            return None

        target_b = ip_address(target_host).packed
        connect_req = b"\x05\x01\x00\x01" + target_b + target_port.to_bytes(2, "big")
        writer.write(connect_req)
        await writer.drain()

        resp = await asyncio.wait_for(reader.readexactly(4), timeout=timeout_seconds)
        if resp[0] != 0x05 or resp[1] != 0x00:
            return None
        atyp = resp[3]
        if atyp == 0x01:
            await asyncio.wait_for(reader.readexactly(6), timeout=timeout_seconds)
        elif atyp == 0x03:
            domain_len = await asyncio.wait_for(reader.readexactly(1), timeout=timeout_seconds)
            await asyncio.wait_for(reader.readexactly(domain_len[0] + 2), timeout=timeout_seconds)
        elif atyp == 0x04:
            await asyncio.wait_for(reader.readexactly(18), timeout=timeout_seconds)
        else:
            return None
        return (loop.time() - started) * 1000
    except Exception:
        return None
    finally:
        writer.close()
        await writer.wait_closed()


async def get_server_status(sub: Subscription) -> ServerStatus:
    ping_ms, (tcp_available, tcp_latency_ms), auth_available, telegram_latency_ms = await asyncio.gather(
        _measure_ping_ms(sub.host),
        _measure_tcp_latency_ms(sub.host, sub.port),
        _probe_socks_auth(sub.host, sub.port, sub.username, sub.password),
        _measure_telegram_via_socks_latency_ms(sub.host, sub.port, sub.username, sub.password),
    )
    if not tcp_available:
        auth_available = None
        telegram_latency_ms = None
    return ServerStatus(
        host=sub.host,
        port=sub.port,
        checked_at=now_utc(),
        ping_ms=ping_ms,
        tcp_latency_ms=tcp_latency_ms,
        telegram_latency_ms=telegram_latency_ms,
        tcp_available=tcp_available,
        auth_available=auth_available,
    )
