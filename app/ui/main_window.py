from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("STARZ Order Manager")
        self.resize(1200, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        title = QLabel("STARZ ORDER MANAGER")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            padding: 20px;
        """)

        layout.addWidget(title)

        layout.addWidget(QPushButton("Dashboard"))
        layout.addWidget(QPushButton("Nouvelles commandes"))
        layout.addWidget(QPushButton("BLOG Digital"))
        layout.addWidget(QPushButton("Stock"))
        layout.addWidget(QPushButton("ERP"))
        layout.addWidget(QPushButton("Paramètres"))

        layout.addStretch()