"""Reusable command palette and workspace activity panels."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import QAbstractItemView, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QStyledItemDelegate, QStyle, QVBoxLayout, QWidget

from forge.core.actions import ActionSpec
from forge.core.config import TimelineEvent
from forge.core.insights import WorkspaceInsight
from forge.desktop.components import ForgeButton, SectionHeader, StatusIndicator
from forge.desktop.theme import THEME

_SPACE = THEME.spacing
_GEOMETRY = THEME.geometry
_TYPE = THEME.typography


class CommandPalette(QDialog):
    """Keyboard-first searchable action picker."""

    selected = Signal(object)

    def __init__(self, actions: tuple[ActionSpec, ...], parent: QWidget | None = None):
        super().__init__(parent)
        self.actions = actions
        self.setWindowTitle("Forge Command Palette")
        self.setModal(True)
        self.setMinimumWidth(_GEOMETRY.palette_min_width)
        self.setObjectName("commandPalette")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(_SPACE.large, _SPACE.large, _SPACE.large, _SPACE.medium)
        layout.setSpacing(_SPACE.medium)
        heading = QHBoxLayout()
        label = QLabel("COMMAND PALETTE  /  FORGE")
        label.setObjectName("eyebrow")
        heading.addWidget(label)
        heading.addStretch(1)
        hint = QLabel("ESC TO CLOSE")
        hint.setObjectName("mutedText")
        heading.addWidget(hint)
        layout.addLayout(heading)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Type a command or project task")
        self.search.setClearButtonEnabled(True)
        self.search.installEventFilter(self)
        layout.addWidget(self.search)
        self.results = QListWidget()
        self.results.setObjectName("paletteResults")
        self.results.setMinimumHeight(_GEOMETRY.palette_min_height)
        self.results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.results.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results.setItemDelegate(ActionItemDelegate(self.results))
        layout.addWidget(self.results)
        keyboard_hint = QLabel("↑ ↓  SELECT     ENTER  RUN     CTRL+K  TOGGLE")
        keyboard_hint.setObjectName("eyebrow")
        layout.addWidget(keyboard_hint)
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
                item = QListWidgetItem(action.title)
                item.setData(Qt.ItemDataRole.UserRole, action)
                item.setToolTip(action.description)
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


class ActionItemDelegate(QStyledItemDelegate):
    """Paint command title, category, and hint with palette hierarchy."""

    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), _SPACE.xxlarge + _SPACE.xlarge)

    def paint(self, painter: QPainter, option, index) -> None:
        action = index.data(Qt.ItemDataRole.UserRole)
        if action is None:
            return
        painter.save()
        rect = option.rect
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        colors = THEME.colors
        if selected:
            painter.fillRect(rect, QColor(colors.accent_soft))
            painter.fillRect(rect.left(), rect.top(), THEME.geometry.focus_width, rect.height(), QColor(colors.accent))
        elif hovered:
            painter.fillRect(rect, QColor(colors.surface_elevated))

        left = rect.left() + _SPACE.large
        right = rect.right() - _SPACE.large
        title_font = QFont(option.font)
        title_font.setPointSize(_TYPE.body)
        title_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor(colors.text_primary if selected else colors.text_secondary))
        title_rect = rect.adjusted(left - rect.left(), _SPACE.xsmall,
                                   -(_SPACE.large + _GEOMETRY.palette_category_width), -rect.height() // 2)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, action.title)

        category_font = QFont(option.font)
        category_font.setPointSize(_TYPE.metadata)
        category_font.setWeight(QFont.Weight.Bold)
        painter.setFont(category_font)
        painter.setPen(QColor(colors.accent if selected else colors.text_muted))
        category_rect = rect.adjusted(0, _SPACE.xsmall,
                                     -_SPACE.large, -rect.height() // 2)
        painter.drawText(category_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                         action.category.upper())

        hint_font = QFont(option.font)
        hint_font.setPointSize(_TYPE.secondary)
        painter.setFont(hint_font)
        painter.setPen(QColor(colors.text_muted))
        hint_rect = rect.adjusted(left - rect.left(), rect.height() // 2 - _SPACE.xsmall, -_SPACE.large, -_SPACE.xsmall)
        painter.drawText(hint_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         painter.fontMetrics().elidedText(action.description, Qt.TextElideMode.ElideRight, hint_rect.width()))
        painter.restore()


class InsightList(QFrame):
    """Compact list of context-derived suggestions."""

    actionRequested = Signal(str)

    def __init__(self, insights: tuple[WorkspaceInsight, ...], parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("insightPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*([_SPACE.panel_padding] * 4))
        layout.setSpacing(_SPACE.small)
        layout.addWidget(SectionHeader("Workspace pulse", f"{len(insights)} OBSERVATION(S)"))
        if not insights:
            empty = QLabel("Workspace looks ready. Choose an action to get moving.")
            empty.setObjectName("mutedText")
            layout.addWidget(empty)
        for insight in insights[:5]:
            row = QHBoxLayout()
            row.setSpacing(_SPACE.medium)
            marker = QLabel("●")
            marker.setObjectName({"success": "pulseSuccess", "warning": "pulseWarning", "error": "pulseError"}.get(
                insight.tone, "pulseInfo"))
            row.addWidget(marker, 0, Qt.AlignmentFlag.AlignTop)
            copy = QVBoxLayout()
            copy.setSpacing(_SPACE.xsmall // 2)
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
        layout.setContentsMargins(*([_SPACE.panel_padding] * 4))
        layout.setSpacing(_SPACE.medium)
        layout.addWidget(SectionHeader("Actions", activity.upper()))
        selected = self._for_activity(actions, activity)
        grid = QGridLayout()
        grid.setHorizontalSpacing(_SPACE.small)
        grid.setVerticalSpacing(_SPACE.small)
        self._action_grid = grid
        self._action_buttons: list[ForgeButton] = []
        self._empty_state: QLabel | None = None
        for action in selected[:8]:
            button = ForgeButton(action.title)
            button.setToolTip(action.description)
            button.clicked.connect(lambda checked=False, selected_action=action:
                                   self.actionRequested.emit(selected_action))
            self._action_buttons.append(button)
        if not selected:
            self._empty_state = QLabel("No actions match this activity yet. Add argv tasks in .forge/tasks.json.")
            self._empty_state.setObjectName("mutedText")
        layout.addLayout(grid)
        self._columns = 0
        self._reflow_actions()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reflow_actions()

    def _reflow_actions(self) -> None:
        columns = 2 if self.width() < 840 else 3 if self.width() < 1040 else 4
        if columns == self._columns:
            return
        while self._action_grid.count():
            self._action_grid.takeAt(0)
        if not self._action_buttons and self._empty_state is not None:
            self._action_grid.addWidget(self._empty_state, 0, 0, 1, columns)
        for index, button in enumerate(self._action_buttons):
            self._action_grid.addWidget(button, index // columns, index % columns)
        self._columns = columns

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

    def __init__(self, events: list[TimelineEvent], project_name: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("surfaceCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*([_SPACE.panel_padding] * 4))
        layout.setSpacing(_SPACE.small)
        detail = f"{project_name.upper()}  /  LOG" if project_name else "LOCAL LOG"
        layout.addWidget(SectionHeader("Recent activity", detail))
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
            time_label.setObjectName("timelineTime")
            time_label.setFixedWidth(_SPACE.xxlarge + _SPACE.medium)
            kind = QLabel(_event_kind(event.message))
            kind.setObjectName("eventType")
            kind.setProperty("tone", event.tone if event.tone in {"success", "warning", "error"} else "info")
            message = QLabel(event.message)
            message.setObjectName("bodyText")
            message.setWordWrap(True)
            row.addWidget(time_label)
            row.addWidget(kind)
            row.addWidget(message, 1)
            layout.addLayout(row)


class ActionOutput(QWidget):
    """Bounded live output area for active and completed actions."""

    stopRequested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(_SPACE.small, _SPACE.xsmall, _SPACE.small, _SPACE.small)
        layout.setSpacing(_SPACE.small)
        top = QHBoxLayout()
        self.title = QLabel("Action output")
        self.title.setObjectName("sectionTitle")
        top.addWidget(self.title)
        self.status = StatusIndicator("IDLE", "info")
        top.addWidget(self.status)
        top.addStretch(1)
        self.stop_button = ForgeButton("Stop all actions", "destructiveButton")
        self.stop_button.clicked.connect(self.stopRequested)
        self.stop_button.hide()
        top.addWidget(self.stop_button)
        layout.addLayout(top)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(_GEOMETRY.output_max_blocks)
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
        self.status.set_status(f"RUNNING · {len(self._running)}", "info")
        self.append(f"\n$ {command or title}\n")
        self.stop_button.show()

    def finish(self, token: int, title: str, return_code: int | None, cancelled: bool) -> None:
        self._running.pop(token, None)
        state = "stopped" if cancelled else "finished" if return_code == 0 else f"failed ({return_code})"
        self.title.setText(f"{len(self._running)} actions running" if self._running else f"{title} · {state}")
        self.stop_button.setVisible(bool(self._running))
        if self._running:
            self.status.set_status(f"RUNNING · {len(self._running)}", "info")
        else:
            tone = "warning" if cancelled else "success" if return_code == 0 else "error"
            self.status.set_status("STOPPED" if cancelled else "DONE" if return_code == 0 else "FAILED", tone)


def _event_kind(message: str) -> str:
    normalized = message.casefold()
    if any(word in normalized for word in ("workspace", "project", "session", "change", "file")):
        return "WORKSPACE"
    if "mode" in normalized:
        return "MODE"
    return "ACTION"
