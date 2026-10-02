import sys

from PySide6.QtWidgets import QApplication

from forge.desktop.window import ForgeWindow


def main():
    app = QApplication(sys.argv)

    window = ForgeWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()