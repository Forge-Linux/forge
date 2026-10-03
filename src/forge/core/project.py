"""Best-effort project and Git context detection without UI dependencies."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


PROJECT_MARKERS = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
    "uv.lock",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "CMakeLists.txt",
    "Makefile",
)
VENV_NAMES = (".venv", "venv", "env")


@dataclass(frozen=True)
class GitInfo:
    """Git state for a repository, when Git metadata is readable."""

    repository_root: Path
    current_branch: str | None
    is_clean: bool | None
    changed_files: int | None


@dataclass(frozen=True)
class ProjectInfo:
    """Project context discovered from a filesystem path."""

    project_name: str | None
    project_root: Path | None
    project_files: tuple[str, ...]
    virtual_environment: Path | None
    git: GitInfo | None
    git_available: bool


def _run_git(arguments: list[str], path: Path) -> subprocess.CompletedProcess[str] | None:
    """Run Git with bounded time and return None when it cannot be run."""
    try:
        return subprocess.run(
            ["git", "-C", str(path), *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _find_git(path: Path) -> tuple[GitInfo | None, bool]:
    """Return repository state and whether the Git executable is available."""
    git_path = shutil.which("git")
    if git_path is None:
        return None, False

    root_result = _run_git(["rev-parse", "--show-toplevel"], path)
    if root_result is None or root_result.returncode != 0:
        return None, True
    try:
        root = Path(root_result.stdout.strip()).resolve()
    except (OSError, RuntimeError):
        return None, True

    branch_result = _run_git(["symbolic-ref", "--quiet", "--short", "HEAD"], path)
    branch = branch_result.stdout.strip() if branch_result and branch_result.returncode == 0 else None

    status_result = _run_git(["status", "--porcelain", "--untracked-files=all"], path)
    if status_result is not None and status_result.returncode == 0:
        changed = len(status_result.stdout.splitlines())
        clean: bool | None = changed == 0
    else:
        changed = None
        clean = None

    return GitInfo(root, branch or None, clean, changed), True


def _as_directory(path: Path) -> Path | None:
    """Resolve a path and use its directory, or None if it is inaccessible."""
    try:
        resolved = path.expanduser().resolve(strict=True)
        directory = resolved if resolved.is_dir() else resolved.parent
        if not directory.is_dir() or not os.access(directory, os.R_OK | os.X_OK):
            return None
        return directory
    except (OSError, RuntimeError):
        return None


def _project_root(start: Path, git: GitInfo | None) -> Path:
    """Choose the repository root or nearest ancestor with a project marker."""
    if git is not None:
        return git.repository_root
    for directory in (start, *start.parents):
        try:
            if any((directory / marker).is_file() for marker in PROJECT_MARKERS):
                return directory
        except OSError:
            continue
    return start


def _virtual_environment(root: Path) -> Path | None:
    """Find a project-local or active Python virtual environment."""
    active = os.environ.get("VIRTUAL_ENV")
    if active:
        try:
            active_path = Path(active).expanduser().resolve()
            if active_path.is_dir():
                return active_path
        except (OSError, RuntimeError):
            pass
    for name in VENV_NAMES:
        candidate = root / name
        try:
            if candidate.is_dir():
                return candidate.resolve()
        except (OSError, RuntimeError):
            continue
    return None


def detect_project(path: str | os.PathLike[str]) -> ProjectInfo:
    """Detect project files, a Python environment, and Git state at ``path``.

    ``path`` may name a directory or a file inside one. Missing, inaccessible,
    non-project, and non-Git paths produce a result with optional fields empty
    rather than raising. Git operations have a short timeout.
    """
    try:
        requested_path = Path(path)
    except (TypeError, ValueError):
        return ProjectInfo(None, None, (), None, None, shutil.which("git") is not None)

    start = _as_directory(requested_path)
    git_available = shutil.which("git") is not None
    if start is None:
        return ProjectInfo(None, None, (), None, None, git_available)

    git, git_available = _find_git(start)
    root = _project_root(start, git)
    files = tuple(marker for marker in PROJECT_MARKERS if (root / marker).is_file())
    return ProjectInfo(
        project_name=root.name or str(root),
        project_root=root,
        project_files=files,
        virtual_environment=_virtual_environment(root),
        git=git,
        git_available=git_available,
    )
