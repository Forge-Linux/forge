"""Short, event-driven Qt animations used by the Forge presentation layer."""

from __future__ import annotations

import os

from PySide6.QtCore import QEasingCurve, QPauseAnimation, QPropertyAnimation, QSequentialAnimationGroup
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget


def reduced_motion_enabled(preference: bool = False) -> bool:
    """Honor Forge preference and common environment-level animation opt-outs."""
    return preference or os.environ.get("FORGE_REDUCED_MOTION", "").lower() in {"1", "true", "yes"}


def fade_in(widget: QWidget, duration_ms: int = 220, delay_ms: int = 0) -> QSequentialAnimationGroup | QPropertyAnimation | None:
    """Fade one widget in once; returns ``None`` when no motion is requested."""
    if duration_ms <= 0:
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


def animate_hover_opacity(effect: QGraphicsOpacityEffect, hovered: bool, duration_ms: int = 110) -> QPropertyAnimation:
    """Animate the subtle resting/hover opacity of a button."""
    animation = QPropertyAnimation(effect, b"opacity", effect)
    animation.setDuration(duration_ms)
    animation.setStartValue(effect.opacity())
    animation.setEndValue(1.0 if hovered else 0.94)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    animation.start()
    return animation
