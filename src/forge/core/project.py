"""Project and Git context detection without UI dependencies."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from forge.core.git import GitInfo, detect_git

PROJECT_MARKERS = (
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile",
    "poetry.lock", "uv.lock", "package.json", "Cargo.toml", "go.mod",
    "CMakeLists.txt", "Makefile", "Gemfile", "composer.json", "pom.xml",
)


@dataclass(frozen=True)
class ProjectInfo:
    """Filesystem details for a project or directory currently in use."""

    project_name: str | None
    project_root: Path | None
    current_path: Path | None
    project_files: tuple[str, ...]
    git: GitInfo | None
    git_available: bool

    @property
    def virtual_environment(self) -> Path | None:
        """Compatibility accessor retained for earlier Forge callers."""
        from forge.core.environment import detect_environment

        return detect_environment(self.project_root, self.current_path).virtual_environment


def _as_directory(path: str | os.PathLike[str]) -> Path | None:
    try:
        resolved = Path(path).expanduser().resolve(strict=True)
        directory = resolved if resolved.is_dir() else resolved.parent
        return directory if directory.is_dir() and os.access(directory, os.R_OK | os.X_OK) else None
    except (OSError, RuntimeError, TypeError, ValueError):
        return None


def _project_root(start: Path, git: GitInfo | None) -> Path:
    if git:
        return git.repository_root
    for directory in (start, *start.parents):
        try:
            if any((directory / marker).is_file() for marker in PROJECT_MARKERS):
                return directory
        except OSError:
            continue
    return start


def detect_project(path: str | os.PathLike[str]) -> ProjectInfo:
    """Describe a directory or file path; inaccessible paths yield empty context."""
    start = _as_directory(path)
    if start is None:
        return ProjectInfo(None, None, None, (), None, detect_git(path).git_available)
    git_context = detect_git(start)
    root = _project_root(start, git_context.git)
    try:
        markers = tuple(marker for marker in PROJECT_MARKERS if (root / marker).is_file())
    except OSError:
        markers = ()
    return ProjectInfo(root.name or str(root), root, start, markers, git_context.git, git_context.git_available)
