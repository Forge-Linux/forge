"""Best-effort Git context provider."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitInfo:
    """Repository state captured from Git without requiring Git at startup."""

    repository_root: Path
    current_branch: str | None
    detached_head: bool
    is_clean: bool | None
    modified_files: tuple[str, ...]
    untracked_files: tuple[str, ...]
    staged_files: tuple[str, ...]
    ahead: int | None = None
    behind: int | None = None

    @property
    def changed_files(self) -> int:
        """Count unique paths in the working tree status."""
        return len(set(self.modified_files) | set(self.untracked_files) | set(self.staged_files))


@dataclass(frozen=True)
class GitDetection:
    git: GitInfo | None
    git_available: bool


def _run(path: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(path), *args], capture_output=True, text=True,
            check=False, timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def detect_git(path: str | Path) -> GitDetection:
    """Return repository state or an unavailable/no-repository result."""
    if shutil.which("git") is None:
        return GitDetection(None, False)
    directory = Path(path)
    root_result = _run(directory, "rev-parse", "--show-toplevel")
    if root_result is None or root_result.returncode:
        return GitDetection(None, True)
    try:
        root = Path(root_result.stdout.strip()).resolve()
    except (OSError, RuntimeError):
        return GitDetection(None, True)

    branch_result = _run(directory, "symbolic-ref", "--quiet", "--short", "HEAD")
    branch = branch_result.stdout.strip() if branch_result and branch_result.returncode == 0 else None
    status = _run(directory, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    modified: set[str] = set()
    untracked: set[str] = set()
    staged: set[str] = set()
    clean: bool | None = None
    if status is not None and status.returncode == 0:
        entries = status.stdout.split("\0")
        i = 0
        while i < len(entries):
            entry = entries[i]
            i += 1
            if len(entry) < 3:
                continue
            flags, name = entry[:2], entry[3:]
            if flags == "??":
                untracked.add(name)
            else:
                if flags[0] not in (" ", "?"):
                    staged.add(name)
                if flags[1] not in (" ", "?"):
                    modified.add(name)
                # Rename/copy status includes a second NUL-delimited path.
                if "R" in flags or "C" in flags:
                    if i < len(entries):
                        i += 1
        clean = not (modified or untracked or staged)

    ahead = behind = None
    counts = _run(directory, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    if counts is not None and counts.returncode == 0:
        try:
            ahead_text, behind_text = counts.stdout.split()
            ahead, behind = int(ahead_text), int(behind_text)
        except (ValueError, TypeError):
            pass
    return GitDetection(GitInfo(root, branch, branch is None, clean, tuple(sorted(modified)),
                                tuple(sorted(untracked)), tuple(sorted(staged)), ahead, behind), True)
