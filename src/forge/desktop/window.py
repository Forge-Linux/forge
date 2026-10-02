from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
)


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

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(development)
        layout.addWidget(entertainment)
        layout.addWidget(other)

        self.setCentralWidget(central)