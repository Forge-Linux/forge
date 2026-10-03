from forge.core.system import get_system_info
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QFormLayout,
)


def _format_bytes(value: int | None) -> str:
    """Format a byte count for a compact UI label."""
    if value is None:
        return "Unavailable"
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if amount < 1024 or unit == "TB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return "Unavailable"


def _format_uptime(seconds: float | None) -> str:
    """Format uptime as days, hours, and minutes."""
    if seconds is None:
        return "Unavailable"
    minutes = int(seconds // 60)
    days, remainder = divmod(minutes, 24 * 60)
    hours, minutes = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m"


class ForgeWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Forge")
        self.resize(1000, 650)

        central = QWidget()
        layout = QVBoxLayout(central)

        title = QLabel("Forge")
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
        """)

        subtitle = QLabel("What are you working on today?")

        development = QPushButton("Development")
        entertainment = QPushButton("Entertainment")
        other = QPushButton("Something else")

        info = get_system_info()
        memory = info["memory"]
        system_section = QGroupBox("System")
        system_layout = QFormLayout(system_section)
        rows = (
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
        for name, value in rows:
            system_layout.addRow(name, QLabel(value or "Unavailable"))

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(development)
        layout.addWidget(entertainment)
        layout.addWidget(other)
        layout.addWidget(system_section)
        layout.addStretch()

        self.setCentralWidget(central)
