from pathlib import Path

from PyQt6.QtCore import (
    Qt,
    QTimer
)

from PyQt6.QtGui import (
    QPixmap
)

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSystemTrayIcon,
    QStyle
)

# =========================================================
# PAGES
# =========================================================

from app.ui.dashboard_page import DashboardPage
from app.ui.blog_page import BlogPage
from app.ui.new_orders_page import NewOrdersPage
from app.ui.stock_page import StockPage

# =========================================================
# OUTLOOK
# =========================================================

from app.services.outlook_monitor import (
    OutlookMonitorWorker
)


# =========================================================
# ASSETS
# =========================================================

ASSET_DIR = (
    Path(__file__).resolve().parents[2]
    / "assets"
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ==================================================
        # FENETRE
        # ==================================================

        self.setWindowTitle(
            "STARZ Order Manager"
        )

        self.resize(
            1440,
            900
        )

        self.setMinimumSize(
            1100,
            720
        )

        self.setStyleSheet(
            self._stylesheet()
        )

        # ==================================================
        # ROOT
        # ==================================================

        root = QWidget()

        root.setObjectName(
            "appRoot"
        )

        self.setCentralWidget(
            root
        )

        main_layout = QHBoxLayout(
            root
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(
            0
        )

        # ==================================================
        # SIDEBAR
        # ==================================================

        sidebar = QFrame()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(
            250
        )

        menu_layout = QVBoxLayout(
            sidebar
        )

        menu_layout.setContentsMargins(
            18,
            22,
            18,
            18
        )

        menu_layout.setSpacing(
            8
        )

        # ==================================================
        # LOGO
        # ==================================================

        logo = QLabel()

        logo.setObjectName(
            "brandLogo"
        )

        logo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        logo.setMinimumHeight(
            116
        )

        logo_path = (
            ASSET_DIR
            / "starz.png"
        )

        pixmap = QPixmap(
            str(
                logo_path
            )
        )

        if not pixmap.isNull():

            logo.setPixmap(
                pixmap.scaled(
                    210,
                    116,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )

        else:

            logo.setText(
                "STARZ"
            )

            logo.setAccessibleName(
                "STARZ"
            )

        menu_layout.addWidget(
            logo
        )

        # ==================================================
        # BRAND
        # ==================================================

        brand_caption = QLabel(
            "ORDER MANAGEMENT"
        )

        brand_caption.setObjectName(
            "brandCaption"
        )

        brand_caption.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        menu_layout.addWidget(
            brand_caption
        )

        menu_layout.addSpacing(
            24
        )

        # ==================================================
        # MENU TITRE
        # ==================================================

        section_label = QLabel(
            "MENU PRINCIPAL"
        )

        section_label.setObjectName(
            "sectionLabel"
        )

        menu_layout.addWidget(
            section_label
        )

        menu_layout.addSpacing(
            4
        )

        # ==================================================
        # BOUTONS NAVIGATION
        # ==================================================

        self.dashboard_button = QPushButton(
            "⌂   Dashboard"
        )

        self.new_orders_button = QPushButton(
            "＋   Nouvelles commandes"
        )

        self.blog_button = QPushButton(
            "▤   BLOG Digital"
        )

        self.stock_button = QPushButton(
            "▣   Stock"
        )

        self.erp_button = QPushButton(
            "↗   ERP"
        )

        self.settings_button = QPushButton(
            "⚙   Paramètres"
        )

        self.navigation_buttons = [
            self.dashboard_button,
            self.new_orders_button,
            self.blog_button,
            self.stock_button,
            self.erp_button,
            self.settings_button
        ]

        for index, button in enumerate(
            self.navigation_buttons
        ):

            button.setObjectName(
                "navButton"
            )

            button.setMinimumHeight(
                46
            )

            button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            button.setProperty(
                "active",
                False
            )

            button.clicked.connect(
                lambda checked=False,
                page_index=index:
                self.set_page(
                    page_index
                )
            )

            menu_layout.addWidget(
                button
            )

        menu_layout.addStretch()

        # ==================================================
        # FOOTER SIDEBAR
        # ==================================================

        sidebar_footer = QFrame()

        sidebar_footer.setObjectName(
            "sidebarFooter"
        )

        footer_layout = QVBoxLayout(
            sidebar_footer
        )

        footer_layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        footer_layout.setSpacing(
            3
        )

        footer_title = QLabel(
            "STARZ Electronics"
        )

        footer_title.setObjectName(
            "footerTitle"
        )

        footer_detail = QLabel(
            "Gestion des opérations"
        )

        footer_detail.setObjectName(
            "footerDetail"
        )

        footer_layout.addWidget(
            footer_title
        )

        footer_layout.addWidget(
            footer_detail
        )

        menu_layout.addWidget(
            sidebar_footer
        )

        main_layout.addWidget(
            sidebar
        )

        # ==================================================
        # WORKSPACE
        # ==================================================

        workspace = QWidget()

        workspace.setObjectName(
            "workspace"
        )

        workspace_layout = QVBoxLayout(
            workspace
        )

        workspace_layout.setContentsMargins(
            30,
            25,
            30,
            28
        )

        workspace_layout.setSpacing(
            20
        )

        # ==================================================
        # TOP BAR
        # ==================================================

        topbar = QHBoxLayout()

        heading_layout = QVBoxLayout()

        heading_layout.setSpacing(
            3
        )

        workspace_title = QLabel(
            "Gestion des opérations"
        )

        workspace_title.setObjectName(
            "workspaceTitle"
        )

        workspace_subtitle = QLabel(
            "Commandes, références et disponibilité des stocks"
        )

        workspace_subtitle.setObjectName(
            "workspaceSubtitle"
        )

        heading_layout.addWidget(
            workspace_title
        )

        heading_layout.addWidget(
            workspace_subtitle
        )

        topbar.addLayout(
            heading_layout
        )

        topbar.addStretch()

        # ==================================================
        # STATUS OUTLOOK
        # ==================================================

        self.connection_status = QLabel(
            "●   Outlook actif"
        )

        self.connection_status.setObjectName(
            "connectionStatus"
        )

        topbar.addWidget(
            self.connection_status,
            0,
            Qt.AlignmentFlag.AlignVCenter
        )

        workspace_layout.addLayout(
            topbar
        )

        # ==================================================
        # PANEL PRINCIPAL
        # ==================================================

        content_panel = QFrame()

        content_panel.setObjectName(
            "contentPanel"
        )

        panel_layout = QVBoxLayout(
            content_panel
        )

        panel_layout.setContentsMargins(
            20,
            18,
            20,
            18
        )

        self.pages = QStackedWidget()

        self.pages.setObjectName(
            "pages"
        )

        panel_layout.addWidget(
            self.pages
        )

        workspace_layout.addWidget(
            content_panel,
            1
        )

        # ==================================================
        # CREATION DES PAGES
        # ==================================================

        self.dashboard_page = DashboardPage()

        self.new_orders_page = NewOrdersPage()

        self.blog_page = BlogPage()

        self.stock_page = StockPage()

        self.erp_page = (
            self.create_placeholder(
                "ERP"
            )
        )

        self.settings_page = (
            self.create_placeholder(
                "Paramètres"
            )
        )

        # ==================================================
        # AJOUT DES PAGES
        # ==================================================

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

        main_layout.addWidget(
            workspace,
            1
        )

        # ==================================================
        # PAGE PAR DEFAUT
        # ==================================================

        self.set_page(
            0
        )

        # ==================================================
        # NOTIFICATION WINDOWS
        # ==================================================

        self.tray_icon = None

        if (
            QSystemTrayIcon
            .isSystemTrayAvailable()
        ):

            self.tray_icon = (
                QSystemTrayIcon(
                    self
                )
            )

            notification_icon = (
                self.style()
                .standardIcon(
                    QStyle.StandardPixmap.SP_MessageBoxInformation
                )
            )

            self.tray_icon.setIcon(
                notification_icon
            )

            self.tray_icon.setToolTip(
                "STARZ Order Manager"
            )

            self.tray_icon.show()

        # ==================================================
        # OUTLOOK AUTOMATIQUE
        # ==================================================

        self.outlook_worker = None

        self.outlook_timer = QTimer(
            self
        )

        self.outlook_timer.timeout.connect(
            self.check_outlook
        )

        # Vérification toutes les 60 secondes
        self.outlook_timer.start(
            60_000
        )

        # Premier contrôle 3 secondes après démarrage
        QTimer.singleShot(
            3000,
            self.check_outlook
        )

    # ======================================================
    # CHANGER PAGE
    # ======================================================

    def set_page(
        self,
        index
    ):

        self.pages.setCurrentIndex(
            index
        )

        # --------------------------------------------------
        # DASHBOARD
        # --------------------------------------------------

        if index == 0:

            try:

                self.dashboard_page.refresh_data()

            except Exception as exc:

                print(
                    "[DASHBOARD]",
                    exc
                )

        # --------------------------------------------------
        # BLOG DIGITAL
        # --------------------------------------------------

        if index == 2:

            try:

                if hasattr(
                    self.blog_page,
                    "load_orders"
                ):

                    self.blog_page.load_orders()

            except Exception as exc:

                print(
                    "[BLOG]",
                    exc
                )

        # --------------------------------------------------
        # STOCK
        # --------------------------------------------------

        if index == 3:

            try:

                if not self.stock_page.has_loaded:
                    self.stock_page.load_stock()

            except Exception as exc:

                print(
                    "[STOCK]",
                    exc
                )

        # --------------------------------------------------
        # STYLE NAVIGATION
        # --------------------------------------------------

        for page_index, button in enumerate(
            self.navigation_buttons
        ):

            is_active = (
                page_index
                == index
            )

            button.setProperty(
                "active",
                is_active
            )

            button.style().unpolish(
                button
            )

            button.style().polish(
                button
            )

        # --------------------------------------------------
        # ENLEVER NOTIFICATION BOUTON
        # --------------------------------------------------

        if index == 1:

            self.new_orders_button.setText(
                "＋   Nouvelles commandes"
            )

    # ======================================================
    # CHECK OUTLOOK
    # ======================================================

    def check_outlook(
        self
    ):

        # Ne pas lancer 2 checks en même temps
        if (
            self.outlook_worker
            is not None
            and
            self.outlook_worker.isRunning()
        ):
            return

        self.connection_status.setText(
            "●   Vérification Outlook..."
        )

        self.outlook_worker = (
            OutlookMonitorWorker()
        )

        self.outlook_worker.order_ready.connect(
            self.on_outlook_order
        )

        self.outlook_worker.error.connect(
            self.on_outlook_error
        )

        self.outlook_worker.finished.connect(
            self.on_outlook_finished
        )

        self.outlook_worker.start()

    # ======================================================
    # NOUVELLE COMMANDE OUTLOOK
    # ======================================================

    def on_outlook_order(
        self,
        order
    ):

        # Envoyer vers Nouvelles commandes
        self.new_orders_page.receive_outlook_order(
            order
        )

        # Notification dans menu
        self.new_orders_button.setText(
            "🔔   Nouvelles commandes"
        )

        po_number = order.get(
            "po_number",
            ""
        )

        product = order.get(
            "product",
            ""
        )

        customer = order.get(
            "customer",
            ""
        )

        # --------------------------------------------------
        # NOTIFICATION WINDOWS
        # --------------------------------------------------

        if self.tray_icon is not None:

            self.tray_icon.showMessage(
                "Nouvelle commande reçue",
                (
                    f"Client : {customer}\n"
                    f"PO : {po_number}\n"
                    f"Produit : {product}"
                ),
                QSystemTrayIcon.MessageIcon.Information,
                8000
            )

        # --------------------------------------------------
        # STATUS BAR
        # --------------------------------------------------

        self.statusBar().showMessage(
            (
                "Nouvelle commande Outlook : "
                f"{po_number}"
            ),
            10000
        )

        self.connection_status.setText(
            "●   Nouvelle commande"
        )

    # ======================================================
    # ERREUR OUTLOOK
    # ======================================================

    def on_outlook_error(
        self,
        message
    ):

        print(
            "[OUTLOOK]",
            message
        )

        self.connection_status.setText(
            "●   Outlook indisponible"
        )

        self.statusBar().showMessage(
            message,
            10000
        )

    # ======================================================
    # CHECK OUTLOOK TERMINE
    # ======================================================

    def on_outlook_finished(
        self
    ):

        current_text = (
            self.connection_status
            .text()
            .lower()
        )

        if (
            "indisponible"
            not in current_text
        ):

            self.connection_status.setText(
                "●   Outlook actif"
            )

    # ======================================================
    # PLACEHOLDER
    # ======================================================

    @staticmethod
    def create_placeholder(
        text
    ):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        title = QLabel(
            text
        )

        title.setObjectName(
            "pageTitle"
        )

        layout.addWidget(
            title
        )

        message = QLabel(
            "Cet espace sera bientôt disponible."
        )

        message.setObjectName(
            "placeholderText"
        )

        layout.addWidget(
            message
        )

        layout.addStretch()

        return page

    # ======================================================
    # STYLE
    # ======================================================

    @staticmethod
    def _stylesheet():

        return """
            QMainWindow, QWidget#appRoot {
                background-color: #f3f6fb;
                color: #202b3c;
                font-family: "Segoe UI";
                font-size: 10pt;
            }

            QFrame#sidebar {
                background-color: #ffffff;
                border: none;
                border-right: 1px solid #e7ebf2;
            }

            QLabel#brandLogo {
                background-color: #ffffff;
                border: none;
            }

            QLabel#brandCaption {
                color: #8792a4;
                font-size: 8pt;
                font-weight: 700;
                letter-spacing: 2px;
            }

            QLabel#sectionLabel {
                color: #9aa4b3;
                font-size: 8pt;
                font-weight: 700;
                padding-left: 10px;
            }

            QPushButton#navButton {
                background-color: transparent;
                border: none;
                border-radius: 9px;
                color: #556174;
                font-size: 10pt;
                font-weight: 600;
                padding: 0 12px;
                text-align: left;
            }

            QPushButton#navButton:hover {
                background-color: #f2f5fa;
                color: #1758a5;
            }

            QPushButton#navButton[active="true"] {
                background-color: #eaf1fb;
                color: #1557a5;
                font-weight: 700;
            }

            QFrame#sidebarFooter {
                background-color: #f5f7fb;
                border: 1px solid #e9edf4;
                border-radius: 10px;
            }

            QLabel#footerTitle {
                color: #253246;
                font-size: 9pt;
                font-weight: 700;
            }

            QLabel#footerDetail {
                color: #8792a4;
                font-size: 8pt;
            }

            QLabel#workspaceTitle {
                color: #1c293b;
                font-size: 19pt;
                font-weight: 700;
            }

            QLabel#workspaceSubtitle {
                color: #7b8798;
                font-size: 9pt;
            }

            QLabel#connectionStatus {
                background-color: #e8f5ee;
                border: 1px solid #d6ecdf;
                border-radius: 14px;
                color: #28794b;
                font-size: 9pt;
                font-weight: 600;
                padding: 8px 13px;
            }

            QFrame#contentPanel {
                background-color: #ffffff;
                border: 1px solid #e7ebf2;
                border-radius: 14px;
            }

            QStackedWidget#pages {
                background: transparent;
                border: none;
            }

            QLabel#pageTitle {
                color: #1c293b;
                font-size: 20pt;
                font-weight: 700;
                padding-bottom: 8px;
            }

            QLabel#placeholderText {
                color: #7b8798;
                font-size: 11pt;
            }

            QLabel {
                color: #344054;
            }

            QLineEdit,
            QComboBox,
            QSpinBox,
            QDateEdit {
                background-color: #ffffff;
                border: 1px solid #d9e0ea;
                border-radius: 8px;
                color: #253246;
                min-height: 20px;
                padding: 8px 10px;
                selection-background-color: #1557a5;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus,
            QDateEdit:focus {
                border: 1px solid #4382cf;
            }

            QPushButton {
                background-color: #1557a5;
                border: 1px solid #1557a5;
                border-radius: 8px;
                color: #ffffff;
                font-weight: 600;
                padding: 9px 16px;
            }

            QPushButton:hover {
                background-color: #104987;
                border-color: #104987;
            }

            QPushButton:pressed {
                background-color: #0d3c71;
            }

            QPushButton:disabled {
                background-color: #d8dee8;
                border-color: #d8dee8;
                color: #8792a4;
            }

            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f7f9fc;
                border: 1px solid #e7ebf2;
                border-radius: 8px;
                color: #344054;
                gridline-color: #edf0f5;
                selection-background-color: #eaf1fb;
                selection-color: #164f91;
            }

            QHeaderView::section {
                background-color: #f5f7fb;
                border: none;
                border-bottom: 1px solid #e5eaf1;
                color: #647186;
                font-size: 9pt;
                font-weight: 700;
                padding: 10px 8px;
            }

            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e4e9f0;
                border-radius: 10px;
                margin-top: 12px;
                padding: 16px 12px 12px;
            }

            QGroupBox::title {
                color: #29384d;
                font-weight: 700;
                left: 10px;
                padding: 0 5px;
                subcontrol-origin: margin;
            }

            QScrollBar:vertical {
                background: transparent;
                margin: 2px;
                width: 10px;
            }

            QScrollBar::handle:vertical {
                background: #cbd4e0;
                border-radius: 4px;
                min-height: 24px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QToolTip {
                background-color: #202b3c;
                border: none;
                color: #ffffff;
                padding: 5px 8px;
            }
        """