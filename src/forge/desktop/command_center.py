"""Reusable command palette and workspace activity panels."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from forge.core.actions import ActionSpec
from forge.core.config import TimelineEvent
from forge.core.insights import WorkspaceInsight
from forge.desktop.components import ForgeButton, SectionHeader


class CommandPalette(QDialog):
    """Keyboard-first searchable action picker."""

    selected = Signal(object)

    def __init__(self, actions: tuple[ActionSpec, ...], parent: QWidget | None = None):
        super().__init__(parent)
        self.actions = actions
        self.setWindowTitle("Forge Command Palette")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setObjectName("commandPalette")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 12)
        layout.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search commands…")
        self.search.setClearButtonEnabled(True)
        self.search.installEventFilter(self)
        layout.addWidget(self.search)
        self.results = QListWidget()
        self.results.setObjectName("paletteResults")
        self.results.setMinimumHeight(280)
        layout.addWidget(self.results)
        hint = QLabel("↑ ↓ to navigate     Enter to run     Esc to close")
        hint.setObjectName("mutedText")
        layout.addWidget(hint)
        self.search.textChanged.connect(self._populate)
        self.search.returnPressed.connect(self._activate)
        self.results.itemActivated.connect(lambda _: self._activate())
        self._populate("")
        self.search.setFocus()

    def _populate(self, query: str) -> None:
        self.results.clear()
        needle = query.casefold().strip()
        for action in self.actions:
            text = f"{action.title}   ·   {action.category}   {action.description}"
            if not needle or needle in text.casefold():
                item = QListWidgetItem(f"{action.title}\n{action.description}")
                item.setData(Qt.ItemDataRole.UserRole, action)
                self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)

    def _activate(self) -> None:
        item = self.results.currentItem()
        if item is None:
            return
        self.selected.emit(item.data(Qt.ItemDataRole.UserRole))
        self.accept()

    def eventFilter(self, watched, event) -> bool:
        if watched is self.search and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down) and self.results.count():
                step = -1 if event.key() == Qt.Key.Key_Up else 1
                row = max(0, min(self.results.count() - 1, self.results.currentRow() + step))
                self.results.setCurrentRow(row)
                return True
        return super().eventFilter(watched, event)


class InsightList(QFrame):
    """Compact list of context-derived suggestions."""

    actionRequested = Signal(str)

    def __init__(self, insights: tuple[WorkspaceInsight, ...], parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("surfaceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 16)
        layout.setSpacing(8)
        layout.addWidget(SectionHeader("Workspace pulse", f"{len(insights)} OBSERVATION(S)"))
        if not insights:
            empty = QLabel("Workspace looks ready. Choose an action to get moving.")
            empty.setObjectName("mutedText")
            layout.addWidget(empty)
        for insight in insights[:5]:
            row = QHBoxLayout()
            row.setSpacing(10)
            marker = QLabel("●")
            marker.setObjectName({"success": "pulseSuccess", "warning": "pulseWarning", "error": "pulseError"}.get(
                insight.tone, "pulseInfo"))
            row.addWidget(marker, 0, Qt.AlignmentFlag.AlignTop)
            copy = QVBoxLayout()
            copy.setSpacing(2)
            title = QLabel(insight.title)
            title.setObjectName("metricValue")
            detail = QLabel(insight.detail)
            detail.setObjectName("mutedText")
            detail.setWordWrap(True)
            copy.addWidget(title)
            copy.addWidget(detail)
            row.addLayout(copy, 1)
            if insight.action_id:
                button = ForgeButton("Review", "subtleButton")
                button.clicked.connect(lambda checked=False, identifier=insight.action_id:
                                       self.actionRequested.emit(identifier))
                row.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
            layout.addLayout(row)


class ActionShelf(QFrame):
    """Mode-filtered project tasks presented as direct controls."""

    actionRequested = Signal(object)

    def __init__(self, actions: tuple[ActionSpec, ...], activity: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("surfaceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 16)
        layout.setSpacing(11)
        layout.addWidget(SectionHeader("Actions", activity.upper()))
        selected = self._for_activity(actions, activity)
        grid = QGridLayout()
        grid.setHorizontalSpacing(9)
        grid.setVerticalSpacing(8)
        for index, action in enumerate(selected[:8]):
            button = ForgeButton(action.title)
            button.setToolTip(action.description)
            button.clicked.connect(lambda checked=False, selected_action=action:
                                   self.actionRequested.emit(selected_action))
            grid.addWidget(button, index // 4, index % 4)
        if not selected:
            empty = QLabel("No actions match this activity yet. Add argv tasks in .forge/tasks.json.")
            empty.setObjectName("mutedText")
            grid.addWidget(empty, 0, 0, 1, 4)
        layout.addLayout(grid)

    @staticmethod
    def _for_activity(actions: tuple[ActionSpec, ...], activity: str) -> list[ActionSpec]:
        base = [action for action in actions if action.category == "Workspace"]
        if activity == "Development":
            chosen = base + [action for action in actions if action.category in {"Git", "Development", "Project tasks"}]
        elif activity == "Entertainment":
            chosen = base + [action for action in actions if action.category == "Entertainment"]
        else:
            chosen = base + [action for action in actions if action.category == "Project tasks"]
        return list(dict.fromkeys(chosen))


class TimelineCard(QFrame):
    """Recent Forge actions and workspace events."""

    def __init__(self, events: list[TimelineEvent], parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("surfaceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 16)
        layout.setSpacing(8)
        layout.addWidget(SectionHeader("Recent activity", "LOCAL HISTORY"))
        if not events:
            label = QLabel("Your workspace activity will appear here.")
            label.setObjectName("mutedText")
            layout.addWidget(label)
        for event in events[:6]:
            row = QHBoxLayout()
            try:
                event_time = datetime.fromisoformat(event.timestamp).astimezone().strftime("%H:%M")
            except ValueError:
                event_time = "—"
            time_label = QLabel(event_time)
            time_label.setObjectName("monoText")
            time_label.setFixedWidth(52)
            message = QLabel(event.message)
            message.setObjectName("bodyText")
            message.setWordWrap(True)
            row.addWidget(time_label)
            row.addWidget(message, 1)
            layout.addLayout(row)


class ActionOutput(QWidget):
    """Bounded live output area for active and completed actions."""

    stopRequested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)
        top = QHBoxLayout()
        self.title = QLabel("Action output")
        self.title.setObjectName("sectionTitle")
        top.addWidget(self.title)
        top.addStretch(1)
        self.stop_button = QPushButton("Stop all actions")
        self.stop_button.clicked.connect(self.stopRequested)
        self.stop_button.hide()
        top.addWidget(self.stop_button)
        layout.addLayout(top)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(3000)
        self.text.setObjectName("actionOutput")
        layout.addWidget(self.text, 1)
        self._running: dict[int, str] = {}

    def append(self, text: str) -> None:
        cursor = self.text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        self.text.setTextCursor(cursor)
        self.text.ensureCursorVisible()

    def begin(self, title: str, command: str = "", token: int = 0) -> None:
        self._running[token] = title
        self.title.setText(f"Running · {title}" if len(self._running) == 1 else
                           f"{len(self._running)} actions running")
        self.append(f"\n$ {command or title}\n")
        self.stop_button.show()

    def finish(self, token: int, title: str, return_code: int | None, cancelled: bool) -> None:
        self._running.pop(token, None)
        state = "stopped" if cancelled else "finished" if return_code == 0 else f"failed ({return_code})"
        self.title.setText(f"{len(self._running)} actions running" if self._running else f"{title} · {state}")
        self.stop_button.setVisible(bool(self._running))
