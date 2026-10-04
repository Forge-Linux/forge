"""Short, event-driven Qt animations used by the Forge presentation layer."""

from __future__ import annotations

import os

from PySide6.QtCore import QEasingCurve, QPauseAnimation, QPropertyAnimation, QSequentialAnimationGroup
from PySide6.QtWidgets import QApplication, QGraphicsOpacityEffect, QWidget
from forge.desktop.theme import THEME

_MOTION = THEME.motion


def reduced_motion_enabled(preference: bool = False) -> bool:
    """Honor Forge preference and common environment-level animation opt-outs."""
    return preference or os.environ.get("FORGE_REDUCED_MOTION", "").lower() in {"1", "true", "yes"}


def _motion_allowed() -> bool:
    app = QApplication.instance()
    preference = bool(app.property("forgeReducedMotion")) if app is not None else False
    return not reduced_motion_enabled(preference)


def fade_in(widget: QWidget, duration_ms: int = _MOTION.panel_ms, delay_ms: int = 0) -> QSequentialAnimationGroup | QPropertyAnimation | None:
    """Fade one widget in once; returns ``None`` when no motion is requested."""
    if duration_ms <= 0 or not _motion_allowed():
        return None
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.0)
    widget.setGraphicsEffect(effect)
    fade = QPropertyAnimation(effect, b"opacity")
    fade.setDuration(duration_ms)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(QEasingCurve.Type.OutCubic)
    fade.finished.connect(lambda: widget.setGraphicsEffect(None))
    if delay_ms:
        group = QSequentialAnimationGroup(widget)
        group.addAnimation(QPauseAnimation(delay_ms))
        group.addAnimation(fade)
        group.start()
        return group
    fade.setParent(widget)
    fade.start()
    return fade


def animate_opacity(effect: QGraphicsOpacityEffect, opacity: float, duration_ms: int) -> QPropertyAnimation | None:
    """Animate an existing widget opacity effect, respecting reduced motion."""
    if not _motion_allowed() or duration_ms <= 0:
        effect.setOpacity(opacity)
        return None
    for previous in effect.findChildren(QPropertyAnimation):
        previous.stop()
    animation = QPropertyAnimation(effect, b"opacity", effect)
    animation.setDuration(duration_ms)
    animation.setStartValue(effect.opacity())
    animation.setEndValue(opacity)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start()
    return animation


def animate_hover_opacity(effect: QGraphicsOpacityEffect, hovered: bool, duration_ms: int = _MOTION.hover_ms) -> QPropertyAnimation | None:
    """Animate the subtle resting/hover opacity of a button."""
    return animate_opacity(effect, 1.0 if hovered else 0.94, duration_ms)


def pulse_once(widget: QWidget, duration_ms: int = _MOTION.state_ms) -> QPropertyAnimation | None:
    """Give a changed status one brief brightness pulse without a running timer."""
    if not _motion_allowed() or duration_ms <= 0:
        return None
    effect = QGraphicsOpacityEffect(widget)
    effect.setOpacity(0.68)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity", effect)
    animation.setDuration(duration_ms)
    animation.setStartValue(0.68)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.finished.connect(lambda: widget.setGraphicsEffect(None))
    animation.start()
    return animation
