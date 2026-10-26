from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox
)

from app.database.database import get_connection
from app.ui.background_task import BackgroundTask
from app.ui.order_details_dialog import OrderDetailsDialog


def _fetch_orders(search):
    connection = get_connection()

    try:
        cursor = connection.cursor()
        if search:
            value = f"%{search}%"
            cursor.execute("""
                SELECT
                    id,
                    date,
                    customer_date,
                    po,
                    product,
                    quantity,
                    length,
                    upc,
                    status
                FROM orders
                WHERE
                    po LIKE ?
                    OR product LIKE ?
                    OR upc LIKE ?
                ORDER BY id DESC
            """, (value, value, value))
        else:
            cursor.execute("""
                SELECT
                    id,
                    date,
                    customer_date,
                    po,
                    product,
                    quantity,
                    length,
                    upc,
                    status
                FROM orders
                ORDER BY id DESC
            """)

        return cursor.fetchall()
    finally:
        connection.close()


class BlogPage(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        # ==========================
        # TITRE
        # ==========================

        title = QLabel("BLOG DIGITAL - RJ45")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        """)

        self.layout.addWidget(title)

        # ==========================
        # NOMBRE DE COMMANDES
        # ==========================

        self.count_label = QLabel()
        self.layout.addWidget(self.count_label)

        # ==========================
        # RECHERCHE
        # ==========================

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Rechercher par PO, produit ou UPC..."
        )

        self.search_input.setMinimumHeight(40)

        self.search_input.textChanged.connect(
            self.schedule_search
        )

        self.layout.addWidget(self.search_input)

        # ==========================
        # TABLEAU
        # ==========================

        self.table = QTableWidget()

        # ID + 8 colonnes visibles
        self.table.setColumnCount(9)

        self.table.setHorizontalHeaderLabels([
            "ID",
            "Date",
            "Customer Date",
            "PO",
            "Produit",
            "Qty",
            "mt",
            "UPC",
            "Statut"
        ])

        # On cache l'ID
        self.table.hideColumn(0)

        # Lignes alternées
        self.table.setAlternatingRowColors(True)

        # Sélection ligne complète
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        # Pas de modification directe
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        # Double clic = détail commande
        self.table.cellDoubleClicked.connect(
            self.open_order_details
        )

        self.layout.addWidget(self.table)

        # ==========================
        # DIMENSION DES COLONNES
        # ==========================

        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(0, 0)

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self.load_orders)
        self._orders_worker = None
        self._worker_search = None
        self._loaded_search = None

    # ======================================================
    # RECHERCHE AVEC DELAI
    # ======================================================

    def schedule_search(self):
        self._search_timer.start()

    # ======================================================
    # CHARGER LES COMMANDES EN ARRIERE-PLAN
    # ======================================================

    def load_orders(self):
        search = self.search_input.text().strip()

        if search == self._loaded_search:
            return

        if self._orders_worker is not None:
            return

        self.count_label.setText("Chargement des commandes...")
        self._worker_search = search
        self._orders_worker = BackgroundTask(
            lambda: _fetch_orders(search),
            self
        )
        self._orders_worker.succeeded.connect(self._on_orders_loaded)
        self._orders_worker.failed.connect(self._on_orders_error)
        self._orders_worker.finished.connect(self._on_orders_finished)
        self._orders_worker.finished.connect(self._orders_worker.deleteLater)
        self._orders_worker.start()

    def _on_orders_loaded(self, rows):
        if self._worker_search != self.search_input.text().strip():
            return

        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(rows))
            for row_index, row_data in enumerate(rows):
                for column_index, value in enumerate(row_data):
                    item = QTableWidgetItem(
                        "" if value is None else str(value)
                    )
                    self.table.setItem(row_index, column_index, item)
        finally:
            self.table.setUpdatesEnabled(True)

        self._loaded_search = self._worker_search
        self.count_label.setText(f"{len(rows)} commande(s)")

    def _on_orders_error(self, message):
        if self._worker_search == self.search_input.text().strip():
            self.count_label.setText("Impossible de charger les commandes")
            QMessageBox.critical(
                self,
                "Erreur BLOG Digital",
                message
            )

    def _on_orders_finished(self):
        completed_search = self._worker_search
        self._orders_worker = None
        self._worker_search = None

        current_search = self.search_input.text().strip()
        if current_search != completed_search:
            self.load_orders()

    # ======================================================
    # OUVRIR DETAIL COMMANDE
    # ======================================================

    def open_order_details(self, row, column):

        # ID caché dans colonne 0
        item = self.table.item(row, 0)

        if item is None:
            return

        try:
            order_id = int(item.text())
        except ValueError:
            return

        dialog = OrderDetailsDialog(
            order_id,
            self
        )

        dialog.exec()