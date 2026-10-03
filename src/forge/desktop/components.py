"""Reusable presentation components for the Forge workspace dashboard."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QGraphicsOpacityEffect, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from forge.core.workspace import WorkspaceContext
from forge.desktop.motion import animate_hover_opacity


def _label(text: str, object_name: str, parent: QWidget | None = None) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName(object_name)
    label.setWordWrap(True)
    return label


def _card_layout(card: QFrame) -> QVBoxLayout:
    layout = QVBoxLayout(card)
    layout.setContentsMargins(18, 16, 18, 17)
    layout.setSpacing(12)
    return layout


class ForgeButton(QPushButton):
    """A shared button with keyboard affordances and a short hover response."""

    def __init__(self, text: str, object_name: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        if object_name:
            self.setObjectName(object_name)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(0.94)
        self.setGraphicsEffect(effect)
        self._hover_effect = effect

    def enterEvent(self, event) -> None:
        animate_hover_opacity(self._hover_effect, True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        animate_hover_opacity(self._hover_effect, False)
        super().leaveEvent(event)


class StatusIndicator(QLabel):
    """Compact semantic state chip used for system and Git status."""

    def __init__(self, text: str = "", tone: str = "success", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName(f"status{tone.title()}")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_status(self, text: str, tone: str) -> None:
        self.setText(text)
        self.setObjectName(f"status{tone.title()}")
        self.style().unpolish(self)
        self.style().polish(self)


class ForgeHeader(QWidget):
    """Application identity, machine status, and a restrained brand mark."""

    def __init__(self, system_available: bool, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        mark = QLabel("F")
        mark.setObjectName("brandMark")
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark.setFixedSize(30, 30)
        brand = QLabel("FORGE")
        brand.setObjectName("brandName")
        version = _label("WORKSPACE", "eyebrow")
        layout.addWidget(mark)
        layout.addWidget(brand)
        layout.addWidget(version)
        layout.addStretch(1)
        self.system_status = StatusIndicator("● SYSTEM ONLINE" if system_available else "● SYSTEM PARTIAL",
                                             "success" if system_available else "warning")
        layout.addWidget(self.system_status)


class SectionHeader(QWidget):
    """Small label and optional trailing detail for dashboard sections."""

    def __init__(self, title: str, detail: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        label = _label(title.upper(), "eyebrow")
        layout.addWidget(label)
        layout.addStretch(1)
        if detail:
            layout.addWidget(_label(detail, "mutedText"))


class ProjectCard(QFrame):
    """Primary workspace identity and project path card."""

    def __init__(self, context: WorkspaceContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("heroCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout = _card_layout(self)
        project = context.project
        top = QHBoxLayout()
        top.addWidget(_label("CURRENT PROJECT", "eyebrow"))
        top.addStretch(1)
        git = context.git
        if git is None:
            state, tone = ("GIT UNAVAILABLE" if not project.git_available else "NO REPOSITORY"), "warning"
        elif git.is_clean is True:
            state, tone = "WORKTREE CLEAN", "success"
        elif git.is_clean is False:
            state, tone = f"{git.changed_files} CHANGES", "warning"
        else:
            state, tone = "STATUS UNKNOWN", "warning"
        top.addWidget(StatusIndicator(state, tone))
        layout.addLayout(top)
        name = _label(project.project_name or "No project detected", "projectTitle")
        layout.addWidget(name)
        location = display_path(project.project_root) if project.project_root else "Project root unavailable"
        location_row = QHBoxLayout()
        location_row.addWidget(_label("⌖", "mutedText"))
        location_row.addWidget(_label(location, "monoText"), 1)
        layout.addLayout(location_row)
        footer = QHBoxLayout()
        footer.addWidget(_label("ACTIVE PATH", "metricLabel"))
        footer.addWidget(_label(display_path(project.current_path), "mutedText"), 1)
        files = ", ".join(project.project_files) if project.project_files else "No project metadata"
        footer.addWidget(_label(files, "mutedText"))
        layout.addLayout(footer)


class GitStatus(QFrame):
    """Git branch and categorized working-tree status."""

    def __init__(self, context: WorkspaceContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("surfaceCard")
        layout = _card_layout(self)
        layout.addWidget(SectionHeader("Git", "REPOSITORY"))
        git = context.git
        if git is None:
            self.branch = "Git is unavailable" if not context.project.git_available else "Not a Git repository"
            self.state = "No repository state"
            self.tone = "warning"
            details = "Initialize or open a repository to see branch details."
        else:
            self.branch = git.current_branch or "Detached HEAD"
            self.state = "Clean" if git.is_clean is True else (
                f"{git.changed_files} changed file(s)" if git.is_clean is False else "Status unavailable"
            )
            self.tone = "success" if git.is_clean is True else "warning"
            fragments = []
            if git.staged_files:
                fragments.append(f"{len(git.staged_files)} staged")
            if git.modified_files:
                fragments.append(f"{len(git.modified_files)} modified")
            if git.untracked_files:
                fragments.append(f"{len(git.untracked_files)} untracked")
            if git.ahead is not None and git.behind is not None:
                fragments.append(f"↑ {git.ahead}  ↓ {git.behind}")
            details = "  ·  ".join(fragments) if fragments else "Working tree has no pending changes"
        branch_row = QHBoxLayout()
        branch_row.addWidget(_label("⑂", "monoText"))
        branch_row.addWidget(_label(self.branch, "sectionTitle"), 1)
        branch_row.addWidget(StatusIndicator(self.state.upper(), self.tone))
        layout.addLayout(branch_row)
        layout.addWidget(_label(details, "mutedText"))


class EnvironmentCard(QFrame):
    """Detected toolchain and local virtual environment metadata."""

    def __init__(self, context: WorkspaceContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("surfaceCard")
        layout = _card_layout(self)
        layout.addWidget(SectionHeader("Environment", "DETECTED"))
        env = context.environment
        kinds = [item for item in env.indicators if item != "Python virtual environment"]
        headline = ", ".join(kinds) if kinds else "No toolchain metadata detected"
        layout.addWidget(_label(headline, "sectionTitle"))
        venv = str(env.virtual_environment) if env.virtual_environment else "No Python environment detected"
        layout.addWidget(_label(venv, "monoText"))
        if env.active_virtual_environment and env.active_virtual_environment != env.virtual_environment:
            layout.addWidget(_label(f"Active: {env.active_virtual_environment}", "mutedText"))


class SystemCard(QFrame):
    """Compact host and resource summary built from SystemInfo."""

    def __init__(self, context: WorkspaceContext, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("surfaceCard")
        layout = _card_layout(self)
        layout.addWidget(SectionHeader("System", "HOST SNAPSHOT"))
        info = context.system
        mem = info["memory"]
        values = (
            ("OPERATING SYSTEM", info["operating_system"] or "Unavailable"),
            ("KERNEL", info["kernel_version"] or "Unavailable"),
            ("HOSTNAME", info["hostname"] or "Unavailable"),
            ("ARCHITECTURE", info["architecture"] or "Unavailable"),
            ("DESKTOP / SESSION", " · ".join(v for v in (info["desktop_environment"], info["session_type"]) if v) or "Unavailable"),
            ("MEMORY", f"{format_bytes(mem['used'])} used / {format_bytes(mem['total'])} total"),
            ("MEMORY AVAILABLE", format_bytes(mem["available"])),
            ("UPTIME", format_uptime(info["uptime_seconds"])),
        )
        grid = QGridLayout()
        grid.setHorizontalSpacing(22)
        grid.setVerticalSpacing(14)
        for i, (caption, value) in enumerate(values):
            cell = QVBoxLayout()
            cell.setSpacing(4)
            cell.addWidget(_label(caption, "metricLabel"))
            cell.addWidget(_label(value, "metricValue"))
            grid.addLayout(cell, i // 3, i % 3)
        layout.addLayout(grid)


class ActivitySelector(QWidget):
    """Compact exclusive activity controls with a useful current selection."""

    activityChanged = Signal(str)
    ACTIVITIES = ("Development", "Entertainment", "Something else")

    def __init__(self, active: str = "Development", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(_label("FOCUS", "eyebrow"))
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for activity in self.ACTIVITIES:
            button = ForgeButton(activity, "activityButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, value=activity: self.activityChanged.emit(value))
            self.group.addButton(button)
            layout.addWidget(button)
            if activity == active:
                button.setChecked(True)
        layout.addStretch(1)


class RefreshControl(QWidget):
    """Refresh action with an indeterminate progress rail while work is running."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.button = ForgeButton("↻  Refresh workspace", "primaryButton")
        layout.addWidget(self.button)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

    def set_busy(self, busy: bool) -> None:
        self.button.setEnabled(not busy)
        self.button.setText("◌  Refreshing workspace" if busy else "↻  Refresh workspace")
        self.progress.setVisible(busy)


def format_bytes(value: int | None) -> str:
    if value is None:
        return "Unavailable"
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return "Unavailable"


def format_uptime(seconds: float | None) -> str:
    if seconds is None:
        return "Unavailable"
    minutes = int(seconds // 60)
    days, remainder = divmod(minutes, 24 * 60)
    hours, minutes = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"


def display_path(path: Path | None) -> str:
    if path is None:
        return "Unavailable"
    try:
        return "~" + str(path).removeprefix(str(Path.home())) if path.is_relative_to(Path.home()) else str(path)
    except (OSError, ValueError):
        return str(path)
