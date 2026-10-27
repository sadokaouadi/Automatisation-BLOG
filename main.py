import sys

from PyQt6.QtWidgets import QApplication

from app.ui.main_window import MainWindow
from app.database.database import create_tables


def main():

    create_tables()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()