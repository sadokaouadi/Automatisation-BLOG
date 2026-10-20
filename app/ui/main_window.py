from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget
)

from app.ui.blog_page import BlogPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("STARZ Order Manager")
        self.resize(1400, 850)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # ==========================
        # MENU GAUCHE
        # ==========================

        menu_layout = QVBoxLayout()

        logo = QLabel("STARZ")
        logo.setStyleSheet("""
            font-size: 30px;
            font-weight: bold;
            padding: 20px;
        """)

        menu_layout.addWidget(logo)

        self.dashboard_button = QPushButton(
            "Dashboard"
        )

        self.new_orders_button = QPushButton(
            "Nouvelles commandes"
        )

        self.blog_button = QPushButton(
            "BLOG Digital"
        )

        self.stock_button = QPushButton(
            "Stock"
        )

        self.erp_button = QPushButton(
            "ERP"
        )

        self.settings_button = QPushButton(
            "Paramètres"
        )

        buttons = [
            self.dashboard_button,
            self.new_orders_button,
            self.blog_button,
            self.stock_button,
            self.erp_button,
            self.settings_button
        ]

        for button in buttons:

            button.setMinimumHeight(45)

            menu_layout.addWidget(button)

        menu_layout.addStretch()

        # ==========================
        # PAGES
        # ==========================

        self.pages = QStackedWidget()

        self.dashboard_page = self.create_placeholder(
            "Dashboard"
        )

        self.new_orders_page = self.create_placeholder(
            "Nouvelles commandes"
        )

        self.blog_page = BlogPage()

        self.stock_page = self.create_placeholder(
            "Stock"
        )

        self.erp_page = self.create_placeholder(
            "ERP"
        )

        self.settings_page = self.create_placeholder(
            "Paramètres"
        )

        self.pages.addWidget(
            self.dashboard_page
        )

        self.pages.addWidget(
            self.new_orders_page
        )

        self.pages.addWidget(
            self.blog_page
        )

        self.pages.addWidget(
            self.stock_page
        )

        self.pages.addWidget(
            self.erp_page
        )

        self.pages.addWidget(
            self.settings_page
        )

        # ==========================
        # NAVIGATION
        # ==========================

        self.dashboard_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(0)
        )

        self.new_orders_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(1)
        )

        self.blog_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(2)
        )

        self.stock_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(3)
        )

        self.erp_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(4)
        )

        self.settings_button.clicked.connect(
            lambda: self.pages.setCurrentIndex(5)
        )

        # ==========================

        main_layout.addLayout(
            menu_layout,
            1
        )

        main_layout.addWidget(
            self.pages,
            5
        )

    def create_placeholder(self, text):

        page = QWidget()

        layout = QVBoxLayout(page)

        title = QLabel(text)

        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            padding: 20px;
        """)

        layout.addWidget(title)
        layout.addStretch()

        return page