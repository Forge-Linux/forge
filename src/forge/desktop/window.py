"""Composition root for Forge's Qt workspace dashboard."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLayout, QMainWindow, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from forge.core.config import ForgeState, StateStore
from forge.core.workspace import WorkspaceContext, build_workspace_context
from forge.desktop.components import (
    ActivitySelector, EnvironmentCard, ForgeHeader, ProjectCard, RefreshControl,
    GitStatus, SystemCard,
)
from forge.desktop.motion import fade_in, reduced_motion_enabled
from forge.desktop.theme import stylesheet


class _WorkspaceRefreshThread(QThread):
    """Run context providers away from the Qt event loop."""

    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, path: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.path = path

    def run(self) -> None:
        try:
            self.completed.emit(build_workspace_context(self.path))
        except Exception as error:  # surface unexpected provider failures in the UI
            self.failed.emit(f"Workspace refresh failed: {error}")
        finally:
            self.finished.emit()


class ForgeWindow(QMainWindow):
    """Responsive workspace dashboard backed by a single context snapshot."""

    def __init__(self, context: WorkspaceContext | None = None, state_store: StateStore | None = None):
        super().__init__()
        self.state_store = state_store or StateStore()
        self.state: ForgeState = self.state_store.load()
        self.context = context or build_workspace_context(self.state.last_workspace or Path.cwd())
        self._refresh_thread: QThread | None = None
        self._motion_disabled = reduced_motion_enabled(bool(self.state.preferences.get("reduced_motion", False)))
        active_activity = self.state.preferences.get("activity", "Development")
        if active_activity not in ActivitySelector.ACTIVITIES:
            active_activity = "Development"

        self.setWindowTitle("Forge — Workspace")
        self.setMinimumSize(720, 560)
        self.resize(1040, 780)
        self.setStyleSheet(stylesheet())

        canvas = QWidget()
        canvas.setObjectName("forgeCanvas")
        root_layout = QVBoxLayout(canvas)
        root_layout.setContentsMargins(28, 16, 28, 0)
        root_layout.setSpacing(0)
        system = self.context.system
        system_available = bool(system["operating_system"] and system["kernel_version"] and system["hostname"])
        self.header = ForgeHeader(system_available)
        root_layout.addWidget(self.header)
        rule = QFrame()
        rule.setObjectName("headerRule")
        root_layout.addWidget(rule)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        page = QWidget()
        page.setObjectName("forgeCanvas")
        page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        page_outer = QHBoxLayout(page)
        page_outer.setContentsMargins(0, 0, 0, 0)
        page_outer.addStretch(1)
        self.page = QWidget()
        self.page.setMaximumWidth(1060)
        self.page.setObjectName("forgeCanvas")
        self.page_layout = QVBoxLayout(self.page)
        self.page_layout.setContentsMargins(0, 25, 0, 28)
        self.page_layout.setSpacing(18)
        page_outer.addWidget(self.page)
        page_outer.addStretch(1)
        self.scroll.setWidget(page)
        root_layout.addWidget(self.scroll, 1)
        self.setCentralWidget(canvas)

        self._build_dashboard(active_activity)
        if not self._motion_disabled:
            for index, widget in enumerate(self._animated_sections):
                fade_in(widget, duration_ms=240, delay_ms=index * 65)

    def _build_dashboard(self, active_activity: str) -> None:
        self._clear_layout(self.page_layout)
        title_row = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(self._text("Workspace", "pageTitle"))
        titles.addWidget(self._text("Your project, tools, and machine at a glance.", "bodyText"))
        title_row.addLayout(titles, 1)
        self.refresh_control = RefreshControl()
        self.refresh_control.button.clicked.connect(self.refresh_workspace)
        title_row.addWidget(self.refresh_control, 0, Qt.AlignmentFlag.AlignVCenter)
        self.page_layout.addLayout(title_row)

        self.project_card = ProjectCard(self.context)
        self.page_layout.addWidget(self.project_card)

        detail_row = QHBoxLayout()
        detail_row.setSpacing(14)
        self.git_card = GitStatus(self.context)
        self.environment_card = EnvironmentCard(self.context)
        detail_row.addWidget(self.git_card, 1)
        detail_row.addWidget(self.environment_card, 1)
        self.page_layout.addLayout(detail_row)

        self.system_card = SystemCard(self.context)
        self.page_layout.addWidget(self.system_card)

        focus_row = QHBoxLayout()
        self.activity_selector = ActivitySelector(active_activity)
        self.activity_selector.activityChanged.connect(self._set_activity)
        focus_row.addWidget(self.activity_selector, 1)
        self.focus_status = self._text(f"FOCUS MODE  /  {active_activity.upper()}", "mutedText")
        focus_row.addWidget(self.focus_status, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.page_layout.addLayout(focus_row)
        self.refresh_error = self._text("", "mutedText")
        self.refresh_error.setWordWrap(True)
        self.page_layout.addWidget(self.refresh_error)
        self._animated_sections = [self.project_card, self.git_card, self.environment_card, self.system_card]

    def refresh_workspace(self) -> None:
        """Refresh context asynchronously and transition the dashboard on completion."""
        if self._refresh_thread is not None and self._refresh_thread.isRunning():
            return
        path = self.context.project.current_path or Path.cwd()
        thread = _WorkspaceRefreshThread(path, self)
        thread.completed.connect(self._workspace_refreshed)
        thread.failed.connect(self._refresh_failed)
        thread.finished.connect(self._refresh_finished)
        thread.finished.connect(thread.deleteLater)
        self._refresh_thread = thread
        self.refresh_error.clear()
        self.refresh_control.set_busy(True)
        thread.start()

    @Slot(object)
    def _workspace_refreshed(self, context: WorkspaceContext) -> None:
        self.context = context
        root = context.project.project_root
        if root is not None:
            project_path = str(root)
            self.state.last_workspace = project_path
            self.state.recent_projects = [project_path] + [p for p in self.state.recent_projects if p != project_path]
            self.state.recent_projects = self.state.recent_projects[:10]
        self.state_store.save(self.state)
        active = self.state.preferences.get("activity", "Development")
        if active not in ActivitySelector.ACTIVITIES:
            active = "Development"
        self._build_dashboard(active)
        if not self._motion_disabled:
            for index, widget in enumerate(self._animated_sections):
                fade_in(widget, duration_ms=180, delay_ms=index * 35)

    @Slot(str)
    def _refresh_failed(self, message: str) -> None:
        self.refresh_error.setText(message)

    @Slot()
    def _refresh_finished(self) -> None:
        self.refresh_control.set_busy(False)
        self._refresh_thread = None

    @Slot(str)
    def _set_activity(self, activity: str) -> None:
        self.state.preferences["activity"] = activity
        self.focus_status.setText(f"FOCUS MODE  /  {activity.upper()}")
        self.state_store.save(self.state)

    @staticmethod
    def _text(value: str, object_name: str) -> QLabel:
        label = QLabel(value)
        label.setObjectName(object_name)
        return label

    @staticmethod
    def _clear_layout(layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                ForgeWindow._clear_layout(child_layout)
