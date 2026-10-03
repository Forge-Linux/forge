"""Read basic system context from Python and Linux interfaces."""

from __future__ import annotations

import os
import platform
import socket
from typing import TypedDict


class MemoryInfo(TypedDict):
    """Memory values in bytes; values are ``None`` when unavailable."""

    total: int | None
    available: int | None
    used: int | None


class SystemInfo(TypedDict):
    """A snapshot of useful host and desktop-session information."""

    operating_system: str | None
    kernel_version: str | None
    hostname: str | None
    architecture: str | None
    desktop_environment: str | None
    session_type: str | None
    uptime_seconds: float | None
    memory: MemoryInfo


def _read_meminfo() -> MemoryInfo:
    """Read total and available memory from Linux ``/proc/meminfo``."""
    values: dict[str, int] = {}
    try:
        with open("/proc/meminfo", encoding="ascii") as meminfo:
            for line in meminfo:
                key, separator, remainder = line.partition(":")
                if not separator or key not in {"MemTotal", "MemAvailable"}:
                    continue
                amount = remainder.strip().split()
                if amount:
                    # Linux reports these values in KiB.
                    values[key] = int(amount[0]) * 1024
    except (OSError, ValueError):
        pass

    total = values.get("MemTotal")
    available = values.get("MemAvailable")
    used = max(total - available, 0) if total is not None and available is not None else None
    return {"total": total, "available": available, "used": used}


def _read_uptime() -> float | None:
    """Read uptime in seconds from Linux ``/proc/uptime``."""
    try:
        with open("/proc/uptime", encoding="ascii") as uptime_file:
            return float(uptime_file.read().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def _linux_name() -> str | None:
    """Return a human-readable Linux distribution name when available."""
    if platform.system() != "Linux":
        return platform.system() or None
    try:
        release = platform.freedesktop_os_release()
        return release.get("PRETTY_NAME") or release.get("NAME") or "Linux"
    except (OSError, AttributeError):
        return "Linux"


def get_system_info() -> SystemInfo:
    """Collect a best-effort snapshot of system and desktop information.

    Linux-specific metrics are read from ``/proc``. Missing or inaccessible
    information is returned as ``None`` so callers can present it gracefully.
    """
    desktop = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION")
    session = os.environ.get("XDG_SESSION_TYPE")
    if not session:
        if os.environ.get("WAYLAND_DISPLAY"):
            session = "wayland"
        elif os.environ.get("DISPLAY"):
            session = "x11"

    try:
        hostname = socket.gethostname() or None
    except OSError:
        hostname = None

    return {
        "operating_system": _linux_name(),
        "kernel_version": platform.release() or None,
        "hostname": hostname,
        "architecture": platform.machine() or None,
        "desktop_environment": desktop,
        "session_type": session,
        "uptime_seconds": _read_uptime(),
        "memory": _read_meminfo(),
    }
