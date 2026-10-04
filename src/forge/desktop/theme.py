"""Forge's shared visual tokens and Qt stylesheet."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ForgeColors:
    """Semantic colors used across every Forge surface."""

    background: str = "#F5F3EE"
    surface: str = "#FFFEFB"
    surface_elevated: str = "#FFFFFF"
    panel: str = "#FAF9F5"
    hover: str = "#F0EFF8"
    border: str = "#DEDCD5"
    border_subtle: str = "#EAE8E1"
    frame_edge: str = "#E5E8FF"
    frame_border: str = "#CDD3F5"
    text_primary: str = "#201F1D"
    text_secondary: str = "#5E5B56"
    text_muted: str = "#85817A"
    text_inverse: str = "#FFFFFF"
    accent: str = "#929FF0"
    accent_hover: str = "#7E8CE3"
    accent_pressed: str = "#6876CD"
    accent_soft: str = "#EEF0FF"
    success: str = "#4D805F"
    success_soft: str = "#E8F1E9"
    warning: str = "#96621F"
    warning_soft: str = "#F7EFDF"
    error: str = "#A4514D"
    error_soft: str = "#F7EAE7"
    information: str = "#536A91"
    information_soft: str = "#E9EDF5"


@dataclass(frozen=True)
class ForgeSpacing:
    """Four pixel based spacing scale used by layouts and controls."""

    xsmall: int = 4
    small: int = 8
    medium: int = 12
    large: int = 16
    xlarge: int = 24
    xxlarge: int = 32
    window_horizontal: int = 24
    window_top: int = 18
    panel_padding: int = 16
    panel_gap: int = 14
    section_gap: int = 18


@dataclass(frozen=True)
class ForgeTypography:
    """Shared font families and semantic point sizes."""

    sans: str = "'Inter', 'Noto Sans', 'Cantarell', sans-serif"
    display: str = "'Georgia', 'Noto Serif', 'Liberation Serif', serif"
    mono: str = "'JetBrains Mono', 'Iosevka', 'DejaVu Sans Mono', monospace"
    application: int = 10
    title: int = 32
    project: int = 27
    section: int = 11
    body: int = 10
    secondary: int = 9
    metadata: int = 8
    code: int = 9
    brand: int = 12
    brand_mark: int = 11
    title_weight: int = 500
    semibold_weight: int = 650
    medium_weight: int = 600
    bold_weight: int = 700
    heavy_weight: int = 800
    tracking_brand: float = 1.5
    tracking_meta: float = 1.1


@dataclass(frozen=True)
class ForgeGeometry:
    """Reusable geometry tokens for surfaces, borders, and controls."""

    radius_small: int = 7
    radius_medium: int = 14
    radius_pill: int = 18
    border_width: int = 1
    focus_width: int = 2
    control_height: int = 36
    control_height_small: int = 30
    brand_mark_size: int = 30
    window_min_width: int = 680
    window_min_height: int = 560
    content_max_width: int = 1080
    palette_min_width: int = 520
    palette_min_height: int = 270
    palette_category_width: int = 140
    rule_width: int = 1
    marker_width: int = 2
    progress_height: int = 3
    scroll_width: int = 8
    scroll_handle_min: int = 24
    palette_item_height: int = 56
    progress_radius: int = 1
    output_max_blocks: int = 3000
    status_padding_vertical: int = 4
    status_padding_horizontal: int = 8


@dataclass(frozen=True)
class ForgeMotion:
    """Short, event-driven animation durations in milliseconds."""

    hover_ms: int = 160
    press_ms: int = 90
    panel_ms: int = 390
    refresh_ms: int = 300
    state_ms: int = 280
    stagger_ms: int = 65


@dataclass(frozen=True)
class ForgeTheme:
    colors: ForgeColors = ForgeColors()
    spacing: ForgeSpacing = ForgeSpacing()
    typography: ForgeTypography = ForgeTypography()
    geometry: ForgeGeometry = ForgeGeometry()
    motion: ForgeMotion = ForgeMotion()


THEME = ForgeTheme()


def stylesheet(theme: ForgeTheme = THEME) -> str:
    """Build the single shared application stylesheet from semantic tokens."""
    c, s, t, g = theme.colors, theme.spacing, theme.typography, theme.geometry
    return f"""
        QWidget {{
            color: {c.text_primary};
            font-family: {t.sans};
            font-size: {t.application}pt;
        }}
        QMainWindow {{ background: {c.frame_edge}; }}
        QWidget#forgeFrame {{ background: {c.frame_edge}; border: none; }}
        QWidget#forgeCanvas {{ background: {c.background}; border: {g.border_width}px solid {c.frame_border}; border-radius: {g.radius_medium}px; }}
        QWidget#forgePage {{ background: transparent; border: none; }}
        QScrollArea {{ border: none; background: transparent; }}
        QFrame#surfaceCard {{
            background: {c.surface}; border: {g.border_width}px solid {c.border_subtle};
            border-radius: {g.radius_medium}px;
        }}
        QFrame#heroCard {{
            background: {c.surface}; border: {g.border_width}px solid {c.accent};
            border-radius: {g.radius_medium}px;
        }}
        QFrame#insightPanel {{
            background: {c.panel}; border: {g.border_width}px solid {c.border_subtle};
            border-left: {g.focus_width}px solid {c.information}; border-radius: {g.radius_medium}px;
        }}
        QFrame#headerRule {{ background: {c.border_subtle}; border: none; max-height: {g.rule_width}px; }}
        QFrame#sectionMarker {{ background: {c.accent}; border: none; max-width: {g.marker_width}px; min-width: {g.marker_width}px; }}

        QLabel#brandMark {{
            background: {c.accent_soft}; color: {c.accent}; border: {g.border_width}px solid {c.border};
            border-radius: {g.radius_small}px; font-size: {t.brand_mark}pt; font-weight: {t.heavy_weight};
        }}
        QLabel#brandName {{ color: {c.text_primary}; font-size: {t.brand}pt; font-weight: {t.bold_weight}; letter-spacing: {t.tracking_brand}px; }}
        QLabel#brandMeta {{ color: {c.text_muted}; font-size: {t.metadata}pt; font-weight: {t.semibold_weight}; letter-spacing: {t.tracking_meta}px; }}
        QLabel#eyebrow {{ color: {c.text_muted}; font-size: {t.metadata}pt; font-weight: {t.bold_weight}; letter-spacing: {t.tracking_meta}px; }}
        QLabel#pageTitle {{ color: {c.text_primary}; font-family: {t.display}; font-size: {t.title}pt; font-weight: {t.title_weight}; }}
        QLabel#projectTitle {{ color: {c.text_primary}; font-family: {t.display}; font-size: {t.project}pt; font-weight: {t.title_weight}; }}
        QLabel#sectionTitle {{ color: {c.text_primary}; font-size: {t.section}pt; font-weight: {t.semibold_weight}; }}
        QLabel#bodyText {{ color: {c.text_secondary}; font-size: {t.body}pt; }}
        QLabel#secondaryText {{ color: {c.text_secondary}; font-size: {t.secondary}pt; }}
        QLabel#mutedText {{ color: {c.text_muted}; font-size: {t.secondary}pt; }}
        QLabel#monoText {{ color: {c.text_secondary}; font-family: {t.mono}; font-size: {t.code}pt; }}
        QLabel#metricValue {{ color: {c.text_primary}; font-size: {t.body}pt; font-weight: {t.medium_weight}; }}
        QLabel#metricLabel {{ color: {c.text_muted}; font-size: {t.metadata}pt; font-weight: {t.semibold_weight}; letter-spacing: {t.tracking_meta}px; }}
        QLabel#timelineTime {{ color: {c.text_muted}; font-family: {t.mono}; font-size: {t.metadata}pt; }}
        QLabel#eventType {{ color: {c.text_muted}; font-size: {t.metadata}pt; font-weight: {t.bold_weight}; letter-spacing: {t.tracking_meta}px; }}
        QLabel#eventType[tone="success"] {{ color: {c.success}; }}
        QLabel#eventType[tone="warning"] {{ color: {c.warning}; }}
        QLabel#eventType[tone="error"] {{ color: {c.error}; }}
        QLabel#eventType[tone="info"] {{ color: {c.information}; }}

        QLabel#statusSuccess, QLabel#statusWarning, QLabel#statusError, QLabel#statusInfo {{
            border: {g.border_width}px solid {c.border_subtle}; border-radius: {g.radius_pill}px;
            padding: {g.status_padding_vertical}px {g.status_padding_horizontal}px;
            font-size: {t.metadata}pt; font-weight: {t.bold_weight}; letter-spacing: {t.tracking_meta}px;
        }}
        QLabel#statusSuccess {{ color: {c.success}; background: {c.success_soft}; }}
        QLabel#statusWarning {{ color: {c.warning}; background: {c.warning_soft}; }}
        QLabel#statusError {{ color: {c.error}; background: {c.error_soft}; }}
        QLabel#statusInfo {{ color: {c.information}; background: {c.information_soft}; }}
        QLabel#pulseInfo {{ color: {c.information}; font-size: {t.metadata}pt; }}
        QLabel#pulseSuccess {{ color: {c.success}; font-size: {t.metadata}pt; }}
        QLabel#pulseWarning {{ color: {c.warning}; font-size: {t.metadata}pt; }}
        QLabel#pulseError {{ color: {c.error}; font-size: {t.metadata}pt; }}

        QPushButton {{
            background: {c.surface_elevated}; color: {c.text_secondary};
            border: {g.border_width}px solid {c.border}; border-radius: {g.radius_pill}px;
            min-height: {g.control_height}px; padding: 0 {s.medium}px; font-size: {t.secondary}pt;
            font-weight: {t.medium_weight};
        }}
        QPushButton:hover {{ background: {c.hover}; color: {c.text_primary}; border-color: {c.accent}; }}
        QPushButton:pressed {{ background: {c.accent_pressed}; color: {c.text_primary}; border-color: {c.accent_pressed}; }}
        QPushButton:focus {{ border: {g.focus_width}px solid {c.accent}; }}
        QPushButton:disabled {{ color: {c.text_muted}; background: {c.panel}; border-color: {c.border_subtle}; }}
        QPushButton#secondaryButton {{ background: {c.surface_elevated}; }}
        QPushButton#primaryButton {{ background: {c.text_primary}; color: {c.text_inverse}; border-color: {c.text_primary}; }}
        QPushButton#primaryButton:hover {{ background: {c.accent_pressed}; color: {c.text_inverse}; border-color: {c.accent_pressed}; }}
        QPushButton#primaryButton:pressed {{ background: {c.text_primary}; color: {c.text_inverse}; }}
        QPushButton#subtleButton {{
            background: transparent; color: {c.accent}; border-color: transparent;
            min-height: {g.control_height_small}px; padding: 0 {s.small}px;
        }}
        QPushButton#subtleButton:hover {{ background: {c.accent_soft}; color: {c.accent_hover}; border-color: {c.border}; }}
        QPushButton#destructiveButton {{ color: {c.error}; background: {c.error_soft}; border-color: {c.border_subtle}; }}
        QPushButton#destructiveButton:hover {{ color: {c.text_primary}; background: {c.error}; border-color: {c.error}; }}
        QPushButton#activityButton {{ background: transparent; border-color: transparent; color: {c.text_muted}; }}
        QPushButton#activityButton:hover {{ background: {c.hover}; color: {c.text_primary}; border-color: {c.border}; }}
        QPushButton#activityButton:checked {{ background: {c.accent_soft}; border-color: {c.border}; color: {c.accent}; }}
        QPushButton#activityButton:focus {{ border: {g.focus_width}px solid {c.accent}; }}
        QPushButton#primaryButton:disabled, QPushButton#subtleButton:disabled,
        QPushButton#destructiveButton:disabled, QPushButton#activityButton:disabled {{
            color: {c.text_muted}; background: {c.panel}; border-color: {c.border_subtle};
        }}

        QLineEdit {{
            background: {c.panel}; color: {c.text_primary}; border: {g.border_width}px solid {c.border};
            border-radius: {g.radius_small}px; min-height: {g.control_height}px;
            padding: 0 {s.medium}px; selection-background-color: {c.accent_pressed};
        }}
        QLineEdit:focus {{ border: {g.focus_width}px solid {c.accent}; background: {c.surface}; }}
        QListWidget#paletteResults {{ background: {c.background}; border: {g.border_width}px solid {c.border_subtle}; border-radius: {g.radius_small}px; outline: none; }}
        QListWidget#paletteResults::item {{ color: {c.text_secondary}; padding: {s.medium}px; border-bottom: {g.border_width}px solid {c.border_subtle}; min-height: {g.palette_item_height}px; }}
        QListWidget#paletteResults::item:hover {{ background: {c.hover}; color: {c.text_primary}; }}
        QListWidget#paletteResults::item:selected {{ color: {c.text_primary}; background: {c.accent_soft}; border-left: {g.focus_width}px solid {c.accent}; }}
        QDialog#commandPalette {{ background: {c.surface}; border: {g.border_width}px solid {c.border}; }}
        QDialog, QMessageBox, QInputDialog {{ background: {c.surface}; color: {c.text_primary}; }}
        QComboBox {{
            background: {c.surface_elevated}; color: {c.text_primary}; border: {g.border_width}px solid {c.border};
            border-radius: {g.radius_small}px; min-height: {g.control_height}px; padding: 0 {s.medium}px;
        }}
        QComboBox:hover {{ border-color: {c.accent}; }}
        QComboBox:focus {{ border: {g.focus_width}px solid {c.accent}; }}
        QComboBox::drop-down {{ border: none; width: {g.control_height}px; }}
        QComboBox QAbstractItemView {{ background: {c.panel}; color: {c.text_primary}; selection-background-color: {c.accent_soft}; border: {g.border_width}px solid {c.border}; outline: none; }}
        QDockWidget#actionDock {{ color: {c.text_primary}; font-weight: 600; }}
        QDockWidget::title {{ background: {c.surface}; padding: {s.small}px; border-bottom: {g.border_width}px solid {c.border_subtle}; }}
        QPlainTextEdit#actionOutput {{
            background: {c.panel}; color: {c.text_secondary}; border: {g.border_width}px solid {c.border_subtle};
            border-radius: {g.radius_small}px; font-family: {t.mono}; font-size: {t.code}pt;
            selection-background-color: {c.accent_pressed};
        }}
        QPlainTextEdit#actionOutput:focus {{ border: {g.focus_width}px solid {c.accent}; }}
        QToolTip {{ background: {c.surface_elevated}; color: {c.text_primary}; border: {g.border_width}px solid {c.border}; padding: {s.xsmall}px; }}
        QProgressBar {{ background: {c.border_subtle}; border: none; border-radius: {g.progress_radius}px; max-height: {g.progress_height}px; text-align: center; }}
        QProgressBar::chunk {{ background: {c.accent}; border-radius: {g.progress_radius}px; }}
        QScrollBar:vertical {{ width: {g.scroll_width}px; background: transparent; margin: {s.xsmall // 2}px; }}
        QScrollBar::handle:vertical {{ background: {c.border}; min-height: {g.scroll_handle_min}px; border-radius: {g.radius_small}px; }}
        QScrollBar::handle:vertical:hover {{ background: {c.text_muted}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ height: {g.scroll_width}px; background: transparent; margin: {s.xsmall // 2}px; }}
        QScrollBar::handle:horizontal {{ background: {c.border}; min-width: {g.scroll_handle_min}px; border-radius: {g.radius_small}px; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    """
