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


class BlogPage(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        # Titre
        title = QLabel("BLOG DIGITAL - RJ45")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        """)

        self.layout.addWidget(title)

        # Nombre de commandes
        self.count_label = QLabel()
        self.layout.addWidget(self.count_label)

        # Recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Rechercher par PO, produit ou UPC..."
        )

        self.search_input.setMinimumHeight(40)

        self.search_input.textChanged.connect(
            self.load_orders
        )

        self.layout.addWidget(self.search_input)

        # Tableau
        self.table = QTableWidget()

        self.table.setColumnCount(8)

        self.table.setHorizontalHeaderLabels([
            "Date",
            "Customer Date",
            "PO",
            "Produit",
            "Qty",
            "mt",
            "UPC",
            "Statut"
        ])

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.layout.addWidget(self.table)

        # Dimension des colonnes
        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Stretch
        )

        self.load_orders()

    def load_orders(self):

        search = self.search_input.text().strip()

        connection = get_connection()
        cursor = connection.cursor()

        if search:

            value = f"%{search}%"

            cursor.execute("""
                SELECT
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

        else:

            cursor.execute("""
                SELECT
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

        self.count_label.setText(
            f"{len(rows)} commande(s)"
        )

        self.table.setRowCount(len(rows))

        for row_index, row_data in enumerate(rows):

            for column_index, value in enumerate(row_data):

                if value is None:
                    value = ""

                item = QTableWidgetItem(str(value))

                self.table.setItem(
                    row_index,
                    column_index,
                    item
                )