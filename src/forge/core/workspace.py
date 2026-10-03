"""Compose Forge's independent context providers into a workspace snapshot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from forge.core.git import GitInfo

from forge.core.environment import EnvironmentInfo, detect_environment
from forge.core.project import ProjectInfo, detect_project
from forge.core.system import SystemInfo, get_system_info


@dataclass(frozen=True)
class WorkspaceContext:
    """Unified read-only context for the UI and future agent consumers."""

    system: SystemInfo
    project: ProjectInfo
    git: GitInfo | None
    environment: EnvironmentInfo


def build_workspace_context(path: str | os.PathLike[str] | None = None) -> WorkspaceContext:
    """Refresh system, project/Git, and environment context in one call."""
    project = detect_project(path or Path.cwd())
    return WorkspaceContext(
        system=get_system_info(), project=project, git=project.git,
        environment=detect_environment(project.project_root, project.current_path),
    )
