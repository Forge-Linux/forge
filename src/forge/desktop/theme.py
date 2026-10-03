"""Forge's centralized dark visual system for Qt widgets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForgePalette:
    background: str = "#0b1018"
    surface: str = "#111a26"
    surface_elevated: str = "#172333"
    surface_hover: str = "#1b2a3d"
    border: str = "#263648"
    border_subtle: str = "#1c2938"
    text_primary: str = "#e7eef7"
    text_secondary: str = "#a6b5c7"
    text_muted: str = "#718197"
    accent: str = "#65a9ff"
    accent_strong: str = "#3486e8"
    accent_soft: str = "#162c46"
    success: str = "#56d6a0"
    success_soft: str = "#15352f"
    warning: str = "#f2bc62"
    warning_soft: str = "#3b3020"
    error: str = "#f07878"
    error_soft: str = "#3b222b"


PALETTE = ForgePalette()


def stylesheet() -> str:
    """Return the shared Forge Qt stylesheet, derived only from palette tokens."""
    p = PALETTE
    return f"""
        QWidget {{ color: {p.text_primary}; font-family: 'Inter', 'Noto Sans', sans-serif; font-size: 10pt; }}
        QMainWindow, QWidget#forgeCanvas {{ background: {p.background}; }}
        QScrollArea {{ border: none; background: transparent; }}
        QFrame#surfaceCard {{ background: {p.surface}; border: 1px solid {p.border_subtle}; border-radius: 10px; }}
        QFrame#heroCard {{ background: {p.surface}; border: 1px solid {p.border}; border-radius: 12px; }}
        QFrame#headerRule {{ background: {p.border_subtle}; border: none; max-height: 1px; }}
        QLabel#brandMark {{ background: {p.accent_soft}; color: {p.accent}; border: 1px solid {p.border}; border-radius: 7px; font-size: 12pt; font-weight: 800; }}
        QLabel#brandName {{ color: {p.text_primary}; font-size: 12pt; font-weight: 700; letter-spacing: 1px; }}
        QLabel#eyebrow {{ color: {p.text_muted}; font-size: 8pt; font-weight: 700; letter-spacing: 1.3px; }}
        QLabel#pageTitle {{ color: {p.text_primary}; font-size: 23pt; font-weight: 650; }}
        QLabel#projectTitle {{ color: {p.text_primary}; font-size: 20pt; font-weight: 650; }}
        QLabel#sectionTitle {{ color: {p.text_primary}; font-size: 11pt; font-weight: 650; }}
        QLabel#bodyText {{ color: {p.text_secondary}; }}
        QLabel#mutedText {{ color: {p.text_muted}; font-size: 9pt; }}
        QLabel#monoText {{ color: {p.text_secondary}; font-family: 'JetBrains Mono', 'DejaVu Sans Mono', monospace; font-size: 9pt; }}
        QLabel#metricValue {{ color: {p.text_primary}; font-size: 10pt; font-weight: 600; }}
        QLabel#metricLabel {{ color: {p.text_muted}; font-size: 8pt; font-weight: 600; letter-spacing: .5px; }}
        QLabel#statusSuccess {{ color: {p.success}; background: {p.success_soft}; border: 1px solid {p.border_subtle}; border-radius: 9px; padding: 5px 9px; font-size: 8pt; font-weight: 650; }}
        QLabel#statusWarning {{ color: {p.warning}; background: {p.warning_soft}; border: 1px solid {p.border_subtle}; border-radius: 9px; padding: 5px 9px; font-size: 8pt; font-weight: 650; }}
        QLabel#statusError {{ color: {p.error}; background: {p.error_soft}; border: 1px solid {p.border_subtle}; border-radius: 9px; padding: 5px 9px; font-size: 8pt; font-weight: 650; }}
        QPushButton {{ background: {p.surface_elevated}; color: {p.text_secondary}; border: 1px solid {p.border}; border-radius: 7px; padding: 8px 12px; font-weight: 600; }}
        QPushButton:hover {{ background: {p.surface_hover}; color: {p.text_primary}; border-color: {p.accent}; }}
        QPushButton:pressed {{ background: {p.accent_soft}; }}
        QPushButton:focus {{ border: 1px solid {p.accent}; }}
        QPushButton#primaryButton {{ background: {p.accent_strong}; color: #ffffff; border-color: {p.accent_strong}; }}
        QPushButton#primaryButton:hover {{ background: {p.accent}; border-color: {p.accent}; }}
        QPushButton#activityButton {{ background: transparent; border-color: transparent; color: {p.text_muted}; }}
        QPushButton#activityButton:hover {{ background: {p.surface_hover}; color: {p.text_primary}; border-color: {p.border}; }}
        QPushButton#activityButton:checked {{ background: {p.accent_soft}; border-color: {p.border}; color: {p.accent}; }}
        QPushButton:disabled {{ color: {p.text_muted}; background: {p.surface}; border-color: {p.border_subtle}; }}
        QProgressBar {{ background: {p.border_subtle}; border: none; border-radius: 2px; max-height: 3px; text-align: center; }}
        QProgressBar::chunk {{ background: {p.accent}; border-radius: 2px; }}
        QScrollBar:vertical {{ width: 8px; background: transparent; margin: 2px; }}
        QScrollBar::handle:vertical {{ background: {p.border}; min-height: 24px; border-radius: 4px; }}
        QScrollBar::handle:vertical:hover {{ background: {p.text_muted}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """
