"""Small, defensive JSON backed user state for Forge."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def default_config_path() -> Path:
    """Resolve the standard Linux configuration file location."""
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base).expanduser() if base else Path.home() / ".config") / "forge" / "state.json"


@dataclass
class ForgeState:
    last_workspace: str | None = None
    recent_projects: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)


class StateStore:
    """Load and save Forge's small user state document."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_config_path()

    def load(self) -> ForgeState:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return ForgeState()
            last = raw.get("last_workspace")
            recent = raw.get("recent_projects", [])
            preferences = raw.get("preferences", {})
            return ForgeState(
                last if isinstance(last, str) else None,
                [item for item in recent if isinstance(item, str)] if isinstance(recent, list) else [],
                preferences if isinstance(preferences, dict) else {},
            )
        except (OSError, UnicodeError, json.JSONDecodeError):
            return ForgeState()

    def save(self, state: ForgeState) -> None:
        """Persist supported state; inaccessible paths are handled gracefully."""
        payload = {
            "last_workspace": state.last_workspace,
            "recent_projects": state.recent_projects,
            "preferences": state.preferences,
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            temporary.replace(self.path)
        except (OSError, TypeError, ValueError):
            return
