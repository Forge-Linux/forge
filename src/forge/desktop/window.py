"""Forge desktop composition root for workspace context and actions."""

from __future__ import annotations

import threading
import shlex
from pathlib import Path

from PySide6.QtCore import QThread, Qt, Signal, Slot
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QLayout, QMainWindow, QMessageBox,
    QDockWidget, QInputDialog, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from forge.core.actions import ActionResult, ActionSpec, discover_actions, run_action
from forge.core.config import (
    ForgeState, StateStore, record_timeline, remember_workspace,
)
from forge.core.insights import analyze_workspace
from forge.core.workspace import WorkspaceContext, build_workspace_context
from forge.desktop.command_center import ActionOutput, ActionShelf, CommandPalette, InsightList, TimelineCard
from forge.desktop.components import (
    ActivitySelector, EnvironmentCard, ForgeButton, ForgeHeader, GitStatus,
    ProjectCard, RefreshControl, SystemCard,
)
from forge.desktop.motion import fade_in, reduced_motion_enabled
from forge.desktop.theme import stylesheet


class _WorkspaceRefreshThread(QThread):
    """Run context providers away from the Qt event loop."""

    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, path: Path, parent: QWidget | None = None):
        super().__init__(parent)
        self.path = path

    def run(self) -> None:
        try:
            self.completed.emit(build_workspace_context(self.path))
        except Exception as error:
            self.failed.emit(f"Workspace refresh failed: {error}")


class _ActionThread(QThread):
    """Stream a core action's output without blocking Qt."""

    output = Signal(str)
    completed = Signal(object)

    def __init__(self, action: ActionSpec, parent: QWidget | None = None):
        super().__init__(parent)
        self.action = action
        self.cancel_event = threading.Event()

    def run(self) -> None:
        try:
            result = run_action(self.action, self.output.emit, self.cancel_event)
        except Exception as error:
            message = f"Action failed unexpectedly: {error}"
            self.output.emit(message + "\n")
            result = ActionResult(self.action.identifier, 1, message, 0.0)
        self.completed.emit(result)

    def request_stop(self) -> None:
        self.cancel_event.set()


class ForgeWindow(QMainWindow):
    """Responsive command center backed by a WorkspaceContext snapshot."""

    def __init__(self, context: WorkspaceContext | None = None, state_store: StateStore | None = None):
        super().__init__()
        self.state_store = state_store or StateStore()
        self.state: ForgeState = self.state_store.load()
        self.context = context or build_workspace_context(self.state.last_workspace or Path.cwd())
        self._refresh_thread: _WorkspaceRefreshThread | None = None
        self._action_threads: dict[int, _ActionThread] = {}
        self._motion_disabled = reduced_motion_enabled(bool(self.state.preferences.get("reduced_motion", False)))
        self.active_activity = self._activity_from_state()
        if self.context.project.project_root is not None:
            remember_workspace(self.state, self.context.project.project_root, self.active_activity)
            self.state_store.save(self.state)
        self.setWindowTitle("Forge — Workspace")
        self.setMinimumSize(720, 560)
        self.resize(1040, 820)
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
        self.page_layout.setContentsMargins(0, 22, 0, 28)
        self.page_layout.setSpacing(14)
        page_outer.addWidget(self.page)
        page_outer.addStretch(1)
        self.scroll.setWidget(page)
        root_layout.addWidget(self.scroll, 1)
        self.setCentralWidget(canvas)

        self.output_panel = ActionOutput()
        self.output_panel.stopRequested.connect(self._stop_actions)
        self.output_dock = QDockWidget("Action Output", self)
        self.output_dock.setObjectName("actionDock")
        self.output_dock.setWidget(self.output_panel)
        self.output_dock.setMinimumHeight(190)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.output_dock)
        self.output_dock.hide()

        self.palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.palette_shortcut.activated.connect(self.open_command_palette)
        self._build_dashboard()
        if not self._motion_disabled:
            for index, widget in enumerate(self._animated_sections):
                fade_in(widget, duration_ms=240, delay_ms=index * 55)

    def _activity_from_state(self) -> str:
        activity = self.state.preferences.get("activity", "Development")
        return activity if activity in ActivitySelector.ACTIVITIES else "Development"

    def _available_actions(self) -> tuple[ActionSpec, ...]:
        root = self.context.project.project_root or self.context.project.current_path or Path.home()
        commands = list(discover_actions(self.context))
        commands.extend((
            ActionSpec("refresh_workspace", "Refresh workspace", "Rebuild system and project context.", root),
            ActionSpec("open_project", "Open another project", "Choose a project directory.", root),
            ActionSpec("open_sessions", "Switch workspace session", "Restore a recent project session.", root),
        ))
        if self.context.git is not None:
            commands.append(ActionSpec("create_branch", "Create Git branch", "Create and switch to a new branch.", root))
        return tuple(commands)

    def _build_dashboard(self) -> None:
        self._clear_layout(self.page_layout)
        title_row = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(self._text("Command Center", "pageTitle"))
        titles.addWidget(self._text("Your workspace, ready to move.", "bodyText"))
        title_row.addLayout(titles, 1)
        self.palette_button = ForgeButton("⌘  Commands  ·  Ctrl+K")
        self.palette_button.clicked.connect(self.open_command_palette)
        title_row.addWidget(self.palette_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self.session_button = ForgeButton("⌂  Sessions")
        self.session_button.clicked.connect(self.open_sessions)
        title_row.addWidget(self.session_button, 0, Qt.AlignmentFlag.AlignVCenter)
        self.refresh_control = RefreshControl()
        self.refresh_control.button.clicked.connect(lambda checked=False: self.refresh_workspace())
        title_row.addWidget(self.refresh_control, 0, Qt.AlignmentFlag.AlignVCenter)
        self.page_layout.addLayout(title_row)

        self.action_specs = self._available_actions()
        self.project_card = ProjectCard(self.context)
        self.page_layout.addWidget(self.project_card)

        self.pulse = InsightList(analyze_workspace(self.context))
        self.pulse.actionRequested.connect(self._run_insight_action)
        self.page_layout.addWidget(self.pulse)

        action_row = QHBoxLayout()
        self.activity_selector = ActivitySelector(self.active_activity)
        self.activity_selector.activityChanged.connect(self._set_activity)
        action_row.addWidget(self.activity_selector, 0, Qt.AlignmentFlag.AlignVCenter)
        self.focus_status = self._text(f"MODE  /  {self.active_activity.upper()}", "mutedText")
        action_row.addWidget(self.focus_status, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.page_layout.addLayout(action_row)

        self.action_shelf = ActionShelf(self.action_specs, self.active_activity)
        self.action_shelf.actionRequested.connect(self._dispatch_action)
        self.page_layout.addWidget(self.action_shelf)

        detail_row = QHBoxLayout()
        detail_row.setSpacing(14)
        self.git_card = GitStatus(self.context)
        self.environment_card = EnvironmentCard(self.context)
        detail_row.addWidget(self.git_card, 1)
        detail_row.addWidget(self.environment_card, 1)
        self.page_layout.addLayout(detail_row)

        self.system_card = SystemCard(self.context)
        self.page_layout.addWidget(self.system_card)
        self.timeline_card = TimelineCard(self.state.timeline)
        self.page_layout.addWidget(self.timeline_card)
        self.refresh_error = self._text("", "mutedText")
        self.refresh_error.setWordWrap(True)
        self.page_layout.addWidget(self.refresh_error)
        self._animated_sections = [self.project_card, self.pulse, self.action_shelf,
                                   self.git_card, self.environment_card, self.system_card]

    @Slot()
    def open_command_palette(self) -> None:
        palette = CommandPalette(self._available_actions(), self)
        palette.selected.connect(self._dispatch_action)
        palette.exec()

    @Slot(object)
    def _dispatch_action(self, action: ActionSpec) -> None:
        if action.identifier == "refresh_workspace":
            self.refresh_workspace()
        elif action.identifier == "open_project":
            self.open_project()
        elif action.identifier == "open_sessions":
            self.open_sessions()
        elif action.identifier == "create_branch":
            name, accepted = QInputDialog.getText(self, "Create branch", "New branch name:")
            if accepted and name.strip() and self.context.git is not None:
                branch_action = ActionSpec("create_branch", f"Create branch {name.strip()}",
                                           "Create and switch to the new branch.",
                                           self.context.git.repository_root,
                                           ("git", "-C", str(self.context.git.repository_root), "switch", "-c", name.strip()),
                                           "Git")
                self._start_action(branch_action)
        else:
            self._start_action(action)

    @Slot(str)
    def _run_insight_action(self, identifier: str) -> None:
        action = next((item for item in self._available_actions() if item.identifier == identifier), None)
        if action:
            self._start_action(action)
        elif identifier == "open_project":
            self.open_project()

    def _start_action(self, action: ActionSpec) -> None:
        if not action.argv and not action.detached:
            QMessageBox.information(self, "Action unavailable", "No command is available for this project.")
            return
        worker = _ActionThread(action, self)
        key = id(worker)
        self._action_threads[key] = worker
        worker.output.connect(self.output_panel.append)
        worker.completed.connect(lambda result, worker_key=key: self._action_finished(worker_key, result))
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda worker_key=key: self._action_threads.pop(worker_key, None))
        self.output_panel.begin(action.title, shlex.join(action.argv), key)
        self.output_dock.show()
        self.output_dock.raise_()
        self._record_event(f"Started {action.title}")
        worker.start()

    @Slot(object)
    def _action_finished(self, key: int, result: ActionResult) -> None:
        worker = self._action_threads.get(key)
        title = worker.action.title if worker else result.action_id
        self.output_panel.finish(key, title, result.return_code, result.cancelled)
        tone = "success" if result.return_code == 0 else "warning"
        summary = f"{title} {'stopped' if result.cancelled else 'completed' if result.return_code == 0 else 'failed'}"
        self._record_event(summary, tone)
        if result.action_id in {"review_diff", "run_tests", "lint", "build", "dev_server"}:
            self.refresh_workspace()

    @Slot()
    def _stop_actions(self) -> None:
        for worker in tuple(self._action_threads.values()):
            worker.request_stop()

    def open_project(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Open project", str(Path.home()))
        if selected:
            self.refresh_workspace(Path(selected))

    def open_sessions(self) -> None:
        sessions = self.state.sessions
        if not sessions:
            QMessageBox.information(self, "Workspace sessions", "Open a project to start building your recent sessions.")
            return
        options = [f"{session.name}   ·   {session.project_path}" for session in sessions]
        selected, accepted = QInputDialog.getItem(self, "Switch workspace", "Choose a workspace session:", options, 0, False)
        if accepted and selected:
            index = options.index(selected)
            session = sessions[index]
            self.active_activity = session.activity if session.activity in ActivitySelector.ACTIVITIES else "Development"
            self.state.preferences["activity"] = self.active_activity
            self.state_store.save(self.state)
            self.refresh_workspace(Path(session.project_path))

    def refresh_workspace(self, path: Path | None = None) -> None:
        """Refresh context asynchronously for the current or selected project."""
        if self._refresh_thread is not None and self._refresh_thread.isRunning():
            return
        target = path or self.context.project.current_path or Path.cwd()
        thread = _WorkspaceRefreshThread(target, self)
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
            remember_workspace(self.state, root, self.active_activity)
            record_timeline(self.state, f"Workspace refreshed · {root.name}")
        self.state_store.save(self.state)
        self._build_dashboard()
        if not self._motion_disabled:
            for index, widget in enumerate(self._animated_sections):
                fade_in(widget, duration_ms=180, delay_ms=index * 30)

    @Slot(str)
    def _refresh_failed(self, message: str) -> None:
        self.refresh_error.setText(message)
        self._record_event("Workspace refresh failed", "warning")

    @Slot()
    def _refresh_finished(self) -> None:
        self.refresh_control.set_busy(False)
        self._refresh_thread = None

    @Slot(str)
    def _set_activity(self, activity: str) -> None:
        self.active_activity = activity
        self.state.preferences["activity"] = activity
        self.focus_status.setText(f"MODE  /  {activity.upper()}")
        remember = self.context.project.project_root
        if remember:
            remember_workspace(self.state, remember, activity)
        self._record_event(f"Switched to {activity} mode")
        old = self.action_shelf
        self.action_shelf = ActionShelf(self.action_specs, activity)
        self.page_layout.replaceWidget(old, self.action_shelf)
        self.action_shelf.actionRequested.connect(self._dispatch_action)
        old.deleteLater()

    def _record_event(self, message: str, tone: str = "info") -> None:
        record_timeline(self.state, message, tone)
        self.state_store.save(self.state)
        if hasattr(self, "timeline_card"):
            old = self.timeline_card
            self.timeline_card = TimelineCard(self.state.timeline)
            self.page_layout.replaceWidget(old, self.timeline_card)
            old.deleteLater()

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

    def closeEvent(self, event) -> None:
        for worker in tuple(self._action_threads.values()):
            worker.request_stop()
        for worker in tuple(self._action_threads.values()):
            worker.wait(2600)
        if self._refresh_thread is not None and self._refresh_thread.isRunning():
            self._refresh_thread.wait(1500)
        super().closeEvent(event)
