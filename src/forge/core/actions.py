"""Shell-free project actions and subprocess execution for Forge."""

from __future__ import annotations

import json
import os
import selectors
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from forge.core.workspace import WorkspaceContext


@dataclass(frozen=True)
class ActionSpec:
    """A named operation with argv and a project working directory."""

    identifier: str
    title: str
    description: str
    cwd: Path
    argv: tuple[str, ...] = ()
    category: str = "Workspace"
    detached: bool = False
    long_running: bool = False


@dataclass(frozen=True)
class ActionResult:
    """Completion status and bounded output from an action."""

    action_id: str
    return_code: int | None
    output: str
    duration_seconds: float
    cancelled: bool = False


OutputCallback = Callable[[str], None]


def _root(context: WorkspaceContext) -> Path:
    return context.project.project_root or context.project.current_path or Path.home()


def _python(context: WorkspaceContext) -> str:
    environment = context.environment.virtual_environment
    if environment is not None:
        for name in ("python", "python3"):
            candidate = environment / "bin" / name
            if candidate.is_file():
                return str(candidate)
    return sys.executable or "python3"


def _configured_actions(context: WorkspaceContext) -> list[ActionSpec]:
    """Read optional ``.forge/tasks.json`` argv arrays (never shell strings)."""
    root = _root(context)
    task_file = root / ".forge" / "tasks.json"
    try:
        raw = json.loads(task_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    if not isinstance(raw, list):
        return []
    actions: list[ActionSpec] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        identifier, title, argv = item.get("id"), item.get("title"), item.get("argv")
        if (not isinstance(identifier, str) or not identifier.replace("_", "").replace("-", "").isalnum()
                or not isinstance(title, str) or not isinstance(argv, list) or not argv
                or not all(isinstance(part, str) and part for part in argv)):
            continue
        actions.append(ActionSpec(identifier, title[:80], str(item.get("description", "Project task"))[:200],
                                  root, tuple(argv), "Project tasks"))
    return actions


def discover_actions(context: WorkspaceContext) -> tuple[ActionSpec, ...]:
    """Offer useful launch and project tasks based on observed project metadata."""
    root = _root(context)
    actions = [
        ActionSpec("open_terminal", "Open terminal here", "Launch a terminal in this project.", root, category="Workspace"),
        ActionSpec("open_editor", "Open project in editor", "Launch an installed editor at this project.", root, category="Workspace"),
    ]
    if context.git is not None:
        actions.append(ActionSpec("review_diff", "Review Git diff", "Show staged and unstaged changes.", root,
                                  ("git", "-C", str(root), "diff", "HEAD", "--"), "Git"))
    python = _python(context)
    files = set(context.project.project_files)
    if "pyproject.toml" in files or "requirements.txt" in files or "setup.py" in files or "setup.cfg" in files:
        pytest_configured = "pytest" in _metadata_text(root, "pyproject.toml") or (root / "pytest.ini").is_file()
        if pytest_configured:
            actions.append(ActionSpec("run_tests", "Run Python tests", "Run the project test suite with pytest.",
                                      root, (python, "-m", "pytest", "-q"), "Development"))
        elif (root / "tests").is_dir():
            actions.append(ActionSpec("run_tests", "Run Python tests", "Run unittest discovery.", root,
                                      (python, "-m", "unittest", "discover", "-v"), "Development"))
        if _has_ruff_config(root):
            actions.append(ActionSpec("lint", "Lint Python project", "Run Ruff checks.", root,
                                      (python, "-m", "ruff", "check", "."), "Development"))
            actions.append(ActionSpec("format", "Format Python project", "Apply Ruff formatting.", root,
                                      (python, "-m", "ruff", "format", "."), "Development"))
        elif "[tool.black" in _metadata_text(root, "pyproject.toml"):
            actions.append(ActionSpec("format", "Format Python project", "Apply Black formatting.", root,
                                      (python, "-m", "black", "."), "Development"))
        if "pyproject.toml" in files and ("[build-system]" in _metadata_text(root, "pyproject.toml")):
            actions.append(ActionSpec("build", "Build Python package", "Build source and wheel distributions.", root,
                                      (python, "-m", "build"), "Development"))
        if "manage.py" in _safe_names(root):
            actions.append(ActionSpec("dev_server", "Start Django development server", "Run the Django server.",
                                      root, (python, "manage.py", "runserver"), "Development", long_running=True))
    if "package.json" in files:
        package = _read_json(root / "package.json")
        scripts = package.get("scripts", {}) if isinstance(package, dict) else {}
        manager = "npm"
        if (root / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
            manager = "pnpm"
        elif (root / "yarn.lock").exists() and shutil.which("yarn"):
            manager = "yarn"
        if isinstance(scripts, dict):
            for script, title in (("test", "Run project tests"), ("lint", "Lint project"), ("build", "Build project")):
                if script in scripts:
                    actions.append(ActionSpec(script if script != "test" else "run_tests", title,
                                              f"Run {manager} {script}.", root, (manager, "run", script), "Development"))
            if "format" in scripts:
                actions.append(ActionSpec("format", "Format project", f"Run {manager} format.", root,
                                          (manager, "run", "format"), "Development"))
            server_script = "dev" if "dev" in scripts else "start" if "start" in scripts else None
            if server_script:
                actions.append(ActionSpec("dev_server", "Start development server",
                                          f"Run {manager} {server_script}.", root,
                                          (manager, "run", server_script), "Development", long_running=True))
    if "Cargo.toml" in files:
        actions.extend((
            ActionSpec("run_tests", "Run Rust tests", "Run cargo test.", root, ("cargo", "test"), "Development"),
            ActionSpec("build", "Build Rust project", "Run cargo build.", root, ("cargo", "build"), "Development"),
        ))
    if "go.mod" in files:
        actions.extend((
            ActionSpec("run_tests", "Run Go tests", "Run go test ./....", root, ("go", "test", "./..."), "Development"),
            ActionSpec("build", "Build Go project", "Run go build ./....", root, ("go", "build", "./..."), "Development"),
        ))
    actions = [action for action in actions if not action.argv or action.detached or shutil.which(action.argv[0])]
    for executable, title in (("spotify", "Open Spotify"), ("vlc", "Open VLC"), ("mpv", "Open MPV")):
        if shutil.which(executable):
            actions.append(ActionSpec(f"media_{executable}", title,
                                      f"Launch {executable}.", root, (executable,), "Entertainment", detached=True))
    actions.extend(_configured_actions(context))
    unique: dict[str, ActionSpec] = {}
    for action in actions:
        unique.setdefault(action.identifier, action)
    return tuple(unique.values())


def _metadata_text(root: Path, filename: str) -> str:
    try:
        return (root / filename).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _has_ruff_config(root: Path) -> bool:
    return any((root / marker).exists() for marker in ("ruff.toml", ".ruff.toml")) or "[tool.ruff" in _metadata_text(root, "pyproject.toml")


def _safe_names(root: Path) -> set[str]:
    try:
        return {item.name for item in root.iterdir()}
    except OSError:
        return set()


def _launcher(action: ActionSpec) -> tuple[str, ...] | None:
    if action.detached and action.argv:
        return action.argv
    if action.identifier == "open_terminal":
        options = (
            ("x-terminal-emulator", ()),
            ("gnome-terminal", ("--working-directory", str(action.cwd))),
            ("konsole", ("--workdir", str(action.cwd))),
            ("kitty", ("--directory", str(action.cwd))),
            ("alacritty", ("--working-directory", str(action.cwd))),
            ("xfce4-terminal", ("--working-directory", str(action.cwd))),
            ("wezterm", ("start", "--cwd", str(action.cwd))),
        )
        for executable, args in options:
            if shutil.which(executable):
                return (executable, *args)
        terminal = os.environ.get("TERMINAL")
        if terminal:
            parsed = shlex.split(terminal)
            return tuple(parsed) if parsed else None
    if action.identifier == "open_editor":
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        if editor:
            parsed = shlex.split(editor)
            return (*parsed, str(action.cwd)) if parsed else None
        for executable in ("code", "codium", "zed", "subl", "mousepad"):
            if shutil.which(executable):
                return (executable, str(action.cwd))
    return None


def run_action(
    action: ActionSpec,
    on_output: OutputCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> ActionResult:
    """Run a known argv action, stream output, and never invoke a shell."""
    started = time.monotonic()
    launcher = _launcher(action)
    argv = launcher or action.argv
    if not argv:
        return ActionResult(action.identifier, 127, "No compatible application was found.", 0.0)
    if launcher:
        try:
            subprocess.Popen(argv, cwd=action.cwd, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True, close_fds=True)
            output = f"Launched: {shlex.join(argv)}"
            if on_output:
                on_output(output + "\n")
            return ActionResult(action.identifier, 0, output, time.monotonic() - started)
        except OSError as error:
            return ActionResult(action.identifier, 127, f"Unable to launch application: {error}",
                                time.monotonic() - started)

    try:
        process = subprocess.Popen(argv, cwd=action.cwd, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   start_new_session=True, close_fds=True)
    except OSError as error:
        output = f"Unable to start {argv[0]}: {error}"
        if on_output:
            on_output(output + "\n")
        return ActionResult(action.identifier, 127, output, time.monotonic() - started)

    output_parts: list[str] = []
    output_size = 0
    cancelled = False
    cancel_started: float | None = None
    selector = selectors.DefaultSelector()
    assert process.stdout is not None
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        while selector.get_map():
            if cancel_event is not None and cancel_event.is_set():
                if not cancelled:
                    cancelled = True
                    cancel_started = time.monotonic()
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
            if cancel_started is not None and time.monotonic() - cancel_started > 2:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                cancel_started = None
            for key, _ in selector.select(timeout=0.15):
                chunk = os.read(key.fd, 8192)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                text = chunk.decode("utf-8", errors="replace")
                output_size += len(text)
                if output_size <= 300_000:
                    output_parts.append(text)
                if on_output:
                    on_output(text)
            if process.poll() is not None and not selector.get_map():
                break
        try:
            return_code = process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            return_code = process.wait()
    finally:
        selector.close()
        process.stdout.close()
    output = "".join(output_parts)
    if output_size > 300_000:
        output += "\n[Forge truncated captured output after 300 KB.]\n"
    if cancelled:
        output += "\n[Process stopped by user.]\n"
    return ActionResult(action.identifier, return_code, output, time.monotonic() - started, cancelled)
