"""Observe development metadata and local environments without modifying them."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EnvironmentInfo:
    indicators: tuple[str, ...]
    virtual_environment: Path | None
    active_virtual_environment: Path | None


ENVIRONMENT_MARKERS = (".venv", "venv", "env")
DEVELOPMENT_MARKERS = (
    "pyproject.toml", "requirements.txt", "Pipfile", "poetry.lock", "uv.lock",
    "package.json", "Cargo.toml", "go.mod", "CMakeLists.txt", "Makefile",
    "Gemfile", "composer.json", "pom.xml", "build.gradle", "*.sln",
)


def detect_environment(root: Path | None, current_path: Path | None = None) -> EnvironmentInfo:
    """Return project metadata and Python virtual environment indicators."""
    active: Path | None = None
    raw_active = os.environ.get("VIRTUAL_ENV")
    if raw_active:
        try:
            candidate = Path(raw_active).expanduser().resolve()
            if candidate.is_dir():
                active = candidate
        except (OSError, RuntimeError):
            pass

    venv = active
    if root is not None:
        for name in ENVIRONMENT_MARKERS:
            candidate = root / name
            try:
                if candidate.is_dir():
                    venv = candidate.resolve()
                    break
            except (OSError, RuntimeError):
                continue

    indicators: list[str] = []
    if root is not None:
        for marker in DEVELOPMENT_MARKERS:
            try:
                found = root.glob(marker) if "*" in marker else (root / marker,)
                if any(item.exists() for item in found):
                    indicators.append(marker)
            except OSError:
                continue
    if venv is not None:
        indicators.append("Python virtual environment")
    return EnvironmentInfo(tuple(indicators), venv, active)
