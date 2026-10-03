"""Qt presentation for Forge's workspace context."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QWidget,
)

from forge.core.config import ForgeState, StateStore
from forge.core.system import MemoryInfo
from forge.core.workspace import WorkspaceContext, build_workspace_context


def _format_bytes(value: int | None) -> str:
    if value is None:
        return "Unavailable"
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return "Unavailable"


def _format_uptime(seconds: float | None) -> str:
    if seconds is None:
        return "Unavailable"
    minutes = int(seconds // 60)
    days, remainder = divmod(minutes, 24 * 60)
    hours, minutes = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"


class ForgeWindow(QMainWindow):
    """Main dashboard; context gathering stays in ``forge.core``."""

    def __init__(self, context: WorkspaceContext | None = None, state_store: StateStore | None = None):
        super().__init__()
        self.state_store = state_store or StateStore()
        self.state: ForgeState = self.state_store.load()
        self.context = context or build_workspace_context(self.state.last_workspace or Path.cwd())
        self.setWindowTitle("Forge")
        self.resize(1000, 720)

        central = QWidget()
        layout = QVBoxLayout(central)
        title = QLabel("Forge")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")
        layout.addWidget(title)
        layout.addWidget(QLabel("What are you working on today?"))

        activity = QHBoxLayout()
        for label in ("Development", "Entertainment", "Something else"):
            activity.addWidget(QPushButton(label))
        self.refresh_button = QPushButton("Refresh workspace")
        self.refresh_button.clicked.connect(self.refresh_workspace)
        activity.addWidget(self.refresh_button)
        layout.addLayout(activity)

        self.project_section = QGroupBox("Workspace")
        self.project_layout = QFormLayout(self.project_section)
        layout.addWidget(self.project_section)
        self.system_section = QGroupBox("System")
        self.system_layout = QFormLayout(self.system_section)
        layout.addWidget(self.system_section)
        layout.addStretch()
        self.setCentralWidget(central)
        self._render_context()

    def refresh_workspace(self) -> None:
        """Rebuild context on demand and remember the active project."""
        current = self.context.project.current_path or Path.cwd()
        self.context = build_workspace_context(current)
        root = self.context.project.project_root
        if root is not None:
            self.state.last_workspace = str(root)
            self.state.recent_projects = [str(root)] + [p for p in self.state.recent_projects if p != str(root)]
            self.state.recent_projects = self.state.recent_projects[:10]
        self.state_store.save(self.state)
        self._render_context()

    def _render_context(self) -> None:
        self._clear_form(self.project_layout)
        self._clear_form(self.system_layout)
        project = self.context.project
        git = self.context.git
        if git is None:
            git_state = "Not in a Git repository" if project.git_available else "Git unavailable"
            branch, status = git_state, git_state
        else:
            branch = git.current_branch or "Detached HEAD"
            status = "Clean" if git.is_clean is True else (
                f"{git.changed_files} changed file(s)" if git.is_clean is False else "Unknown"
            )
            details = []
            if git.staged_files:
                details.append(f"{len(git.staged_files)} staged")
            if git.modified_files:
                details.append(f"{len(git.modified_files)} modified")
            if git.untracked_files:
                details.append(f"{len(git.untracked_files)} untracked")
            if git.ahead is not None and git.behind is not None:
                details.append(f"↑{git.ahead} ↓{git.behind}")
            if details:
                status += " (" + ", ".join(details) + ")"
        environment = self.context.environment
        rows = (
            ("Project", project.project_name or "No project detected"),
            ("Project root", str(project.project_root) if project.project_root else "Unavailable"),
            ("Current path", str(project.current_path) if project.current_path else "Unavailable"),
            ("Git branch", branch),
            ("Git status", status),
            ("Project files", ", ".join(project.project_files) or "None detected"),
            ("Environment", ", ".join(environment.indicators) or "No metadata detected"),
            ("Python environment", str(environment.virtual_environment) if environment.virtual_environment else "None detected"),
        )
        for key, value in rows:
            self.project_layout.addRow(key, QLabel(value))

        info = self.context.system
        memory: MemoryInfo = info["memory"]
        system_rows = (
            ("Operating system", info["operating_system"]),
            ("Kernel", info["kernel_version"]),
            ("Hostname", info["hostname"]),
            ("Architecture", info["architecture"]),
            ("Desktop environment", info["desktop_environment"]),
            ("Session", info["session_type"]),
            ("Uptime", _format_uptime(info["uptime_seconds"])),
            ("Memory", f"{_format_bytes(memory['used'])} used / {_format_bytes(memory['total'])} total"),
            ("Memory available", _format_bytes(memory["available"])),
        )
        for key, value in system_rows:
            self.system_layout.addRow(key, QLabel(value or "Unavailable"))

    @staticmethod
    def _clear_form(form: QFormLayout) -> None:
        while form.rowCount():
            form.removeRow(0)
