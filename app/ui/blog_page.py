from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView
)

from app.database.database import get_connection
from app.ui.order_details_dialog import OrderDetailsDialog


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
            self.load_orders
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
            QHeaderView.ResizeMode.ResizeToContents
        )

        # Produit = colonne 4
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Stretch
        )

        # ==========================
        # CHARGEMENT INITIAL
        # ==========================

        self.load_orders()

    # ======================================================
    # CHARGER LES COMMANDES
    # ======================================================

    def load_orders(self):

        search = self.search_input.text().strip()

        connection = get_connection()
        cursor = connection.cursor()

        # ==========================
        # AVEC RECHERCHE
        # ==========================

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
            """, (
                value,
                value,
                value
            ))

        # ==========================
        # SANS RECHERCHE
        # ==========================

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

        rows = cursor.fetchall()

        connection.close()

        # ==========================
        # NOMBRE DE COMMANDES
        # ==========================

        self.count_label.setText(
            f"{len(rows)} commande(s)"
        )

        # ==========================
        # REMPLIR LE TABLEAU
        # ==========================

        self.table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):

            for column_index, value in enumerate(row_data):

                if value is None:
                    value = ""

                item = QTableWidgetItem(
                    str(value)
                )

                self.table.setItem(
                    row_index,
                    column_index,
                    item
                )

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