"""Small, defensive JSON backed user state for Forge."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_config_path() -> Path:
    """Resolve the standard Linux configuration file location."""
    base = os.environ.get("XDG_CONFIG_HOME", "").strip()
    configured = Path(base).expanduser() if base else Path.home() / ".config"
    if not configured.is_absolute():
        configured = Path.home() / ".config"
    return configured / "forge" / "state.json"


def remember_workspace(state: "ForgeState", project_path: Path, activity: str) -> None:
    """Update the recent list and named session metadata for one project."""
    path = str(project_path)
    name = project_path.name or path
    state.last_workspace = path
    state.recent_projects = [path] + [item for item in state.recent_projects if item != path]
    state.recent_projects = state.recent_projects[:10]
    stamp = datetime.now(timezone.utc).isoformat()
    session = next((item for item in state.sessions if item.project_path == path), None)
    if session is None:
        state.sessions.insert(0, WorkspaceSession(path, name, activity, stamp))
    else:
        session.activity = activity
        session.last_opened = stamp
        state.sessions.remove(session)
        state.sessions.insert(0, session)
    state.sessions = state.sessions[:10]


def record_timeline(state: "ForgeState", message: str, tone: str = "info") -> None:
    """Append a local timeline entry and keep the most recent 100."""
    state.timeline.insert(0, TimelineEvent(message, tone=tone))
    state.timeline = state.timeline[:100]


@dataclass
class WorkspaceSession:
    """A remembered project workspace and its last selected activity."""

    project_path: str
    name: str
    activity: str = "Development"
    last_opened: str = ""


@dataclass
class TimelineEvent:
    """A small, local record of an action or workspace change."""

    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tone: str = "info"


@dataclass
class ForgeState:
    last_workspace: str | None = None
    recent_projects: list[str] = field(default_factory=list)
    preferences: dict[str, Any] = field(default_factory=dict)
    sessions: list[WorkspaceSession] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)


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
            sessions = raw.get("sessions", [])
            timeline = raw.get("timeline", [])
            loaded_sessions = [
                WorkspaceSession(
                    item["project_path"], item["name"],
                    item.get("activity", "Development") if isinstance(item.get("activity", "Development"), str) else "Development",
                    item.get("last_opened", "") if isinstance(item.get("last_opened", ""), str) else "",
                )
                for item in sessions if isinstance(item, dict)
                and isinstance(item.get("project_path"), str) and isinstance(item.get("name"), str)
            ] if isinstance(sessions, list) else []
            loaded_timeline = [
                TimelineEvent(item["message"],
                              item.get("timestamp", "") if isinstance(item.get("timestamp", ""), str) else "",
                              item.get("tone", "info") if isinstance(item.get("tone", "info"), str) else "info")
                for item in timeline if isinstance(item, dict) and isinstance(item.get("message"), str)
            ] if isinstance(timeline, list) else []
            return ForgeState(
                last if isinstance(last, str) else None,
                [item for item in recent if isinstance(item, str)] if isinstance(recent, list) else [],
                preferences if isinstance(preferences, dict) else {},
                loaded_sessions,
                loaded_timeline,
            )
        except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            return ForgeState()

    def save(self, state: ForgeState) -> None:
        """Persist supported state; inaccessible paths are handled gracefully."""
        payload = {
            "last_workspace": state.last_workspace,
            "recent_projects": state.recent_projects,
            "preferences": state.preferences,
            "sessions": [session.__dict__ for session in state.sessions],
            "timeline": [event.__dict__ for event in state.timeline],
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            temporary.replace(self.path)
        except (OSError, TypeError, ValueError):
            return
