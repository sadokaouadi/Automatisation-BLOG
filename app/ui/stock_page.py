from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox
)

from app.ui.background_task import BackgroundTask
from app.services.clients.commscope.stock_service import (
    get_all_current_stock
)


class StockPage(QWidget):

    def __init__(self):
        super().__init__()

        self.all_stock = []
        self.has_loaded = False
        self._stock_worker = None

        main_layout = QVBoxLayout(self)

        # ==========================================
        # TITRE
        # ==========================================

        title = QLabel(
            "STOCK - COMMSCOPE / RJ45"
        )

        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            margin-bottom: 10px;
        """)

        main_layout.addWidget(title)

        # ==========================================
        # BARRE RECHERCHE
        # ==========================================

        top_layout = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Rechercher : cable, plug, boot, référence..."
        )

        self.search_input.setMinimumHeight(40)

        self.search_input.textChanged.connect(
            self.filter_stock
        )

        refresh_button = QPushButton(
            "Actualiser"
        )

        refresh_button.setMinimumHeight(40)

        refresh_button.clicked.connect(
            self.load_stock
        )
        self.refresh_button = refresh_button

        top_layout.addWidget(
            self.search_input,
            1
        )

        top_layout.addWidget(
            refresh_button
        )

        main_layout.addLayout(
            top_layout
        )

        # ==========================================
        # NOMBRE COMPOSANTS
        # ==========================================

        self.count_label = QLabel()

        main_layout.addWidget(
            self.count_label
        )

        # ==========================================
        # TABLEAU
        # ==========================================

        self.table = QTableWidget()

        self.table.setColumnCount(3)

        self.table.setHorizontalHeaderLabels([
            "Composant / Référence",
            "Stock actuel",
            "État"
        ])

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setAlternatingRowColors(
            True
        )

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents
        )

        main_layout.addWidget(
            self.table
        )

    # ==============================================
    # CHARGER STOCK
    # ==============================================

    def load_stock(self):

        if self._stock_worker is not None:
            return

        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Chargement...")
        self.count_label.setText("Chargement du stock...")
        self._stock_worker = BackgroundTask(
            get_all_current_stock,
            self
        )
        self._stock_worker.succeeded.connect(self._on_stock_loaded)
        self._stock_worker.failed.connect(self._on_stock_error)
        self._stock_worker.finished.connect(self._on_worker_finished)
        self._stock_worker.finished.connect(self._stock_worker.deleteLater)
        self._stock_worker.start()

    def _on_stock_loaded(self, stock):
        self.all_stock = stock
        self.has_loaded = True
        self.filter_stock()

    def _on_stock_error(self, message):
        QMessageBox.critical(
            self,
            "Erreur Stock",
            message
        )

    def _on_worker_finished(self):
        self._stock_worker = None
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Actualiser")

    # ==============================================
    # FILTRER
    # ==============================================

    def filter_stock(self):

        search = (
            self.search_input
            .text()
            .strip()
            .upper()
        )

        if search:

            rows = [
                item
                for item in self.all_stock
                if search in item["component"].upper()
            ]

        else:

            rows = self.all_stock

        self.display_stock(rows)

    # ==============================================
    # AFFICHER STOCK
    # ==============================================

    def display_stock(self, rows):

        self.count_label.setText(
            f"{len(rows)} composant(s)"
        )

        self.table.setRowCount(
            len(rows)
        )

        MIN_STOCK_WARNING = 1000

        for row_index, component in enumerate(rows):

            name = component["component"]
            stock = component["stock"]

            # ======================================
            # ETAT STOCK
            # ======================================

            if stock is None:

                stock_display = "-"
                status = "⚠ Inconnu"

            elif stock <= 0:

                stock_display = f"{stock:,.2f}"
                status = "🔴 Rupture"

            elif stock < MIN_STOCK_WARNING:

                stock_display = f"{stock:,.2f}"
                status = "🟠 Stock faible"

            else:

                stock_display = f"{stock:,.2f}"
                status = "🟢 Disponible"

            # ======================================
            # REMPLIR TABLEAU
            # ======================================

            values = [
                name,
                stock_display,
                status
            ]

            for column_index, value in enumerate(values):

                self.table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(
                        str(value)
                    )
                )