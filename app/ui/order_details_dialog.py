from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QFormLayout,
    QPushButton,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGroupBox
)

from app.database.database import get_connection
from app.services.rj45_stock_analyzer import analyze_rj45_stock


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BLOG_PATH = (
    PROJECT_ROOT
    / "data"
    / "imports"
    / "BLOG_2026_RJ45.xlsx"
)


class OrderDetailsDialog(QDialog):

    def __init__(self, order_id, parent=None):
        super().__init__(parent)

        self.order_id = order_id

        self.product = None
        self.quantity = None

        self.setWindowTitle("Détail de la commande")
        self.resize(1000, 850)

        main_layout = QVBoxLayout(self)

        # ==================================================
        # TITRE
        # ==================================================

        title = QLabel("DÉTAIL DE LA COMMANDE")

        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        """)

        main_layout.addWidget(title)

        # ==================================================
        # COMMANDE
        # ==================================================

        order_group = QGroupBox("Commande")

        form = QFormLayout(order_group)

        self.date_label = QLabel()
        self.customer_date_label = QLabel()
        self.po_label = QLabel()
        self.product_label = QLabel()
        self.quantity_label = QLabel()
        self.length_label = QLabel()
        self.upc_label = QLabel()
        self.customer_label = QLabel()
        self.status_label = QLabel()

        form.addRow("Date :", self.date_label)
        form.addRow("Customer Date :", self.customer_date_label)
        form.addRow("PO :", self.po_label)
        form.addRow("Produit :", self.product_label)
        form.addRow("Quantité :", self.quantity_label)
        form.addRow("Longueur :", self.length_label)
        form.addRow("UPC :", self.upc_label)
        form.addRow("Client :", self.customer_label)
        form.addRow("Statut :", self.status_label)

        main_layout.addWidget(order_group)

        # ==================================================
        # DOUBLE VERIFICATION
        # ==================================================

        verification_group = QGroupBox(
            "Double vérification"
        )

        verification_layout = QVBoxLayout(
            verification_group
        )

        self.verification_1_label = QLabel()
        self.verification_2_label = QLabel()

        verification_layout.addWidget(
            self.verification_1_label
        )

        verification_layout.addWidget(
            self.verification_2_label
        )

        main_layout.addWidget(
            verification_group
        )

        # ==================================================
        # HISTORIQUE PRODUIT
        # ==================================================

        history_group = QGroupBox(
            "Historique du même produit"
        )

        history_layout = QVBoxLayout(
            history_group
        )

        self.history_table = QTableWidget()

        self.history_table.setColumnCount(5)

        self.history_table.setHorizontalHeaderLabels([
            "Date",
            "PO",
            "Qty",
            "mt",
            "UPC"
        ])

        self.history_table.setMaximumHeight(180)

        self.history_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        history_layout.addWidget(
            self.history_table
        )

        main_layout.addWidget(
            history_group
        )

        # ==================================================
        # ANALYSE MATIERE
        # ==================================================

        stock_group = QGroupBox(
            "Analyse matière / stock"
        )

        stock_layout = QVBoxLayout(
            stock_group
        )

        self.stock_status_label = QLabel(
            "Analyse en attente..."
        )

        self.stock_status_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            padding: 8px;
        """)

        stock_layout.addWidget(
            self.stock_status_label
        )

        self.stock_table = QTableWidget()

        self.stock_table.setColumnCount(6)

        self.stock_table.setHorizontalHeaderLabels([
            "Composant",
            "Conso / produit",
            "Stock actuel",
            "Besoin",
            "Stock après",
            "État"
        ])

        self.stock_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.stock_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        header = self.stock_table.horizontalHeader()

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch
        )

        stock_layout.addWidget(
            self.stock_table
        )

        main_layout.addWidget(
            stock_group
        )

        # ==================================================
        # FERMER
        # ==================================================

        close_button = QPushButton(
            "Fermer"
        )

        close_button.setMinimumHeight(40)

        close_button.clicked.connect(
            self.close
        )

        main_layout.addWidget(
            close_button
        )

        # ==================================================
        # CHARGEMENT
        # ==================================================

        self.load_order()

        if self.product:
            self.load_history()

        if self.product and self.quantity:
            self.load_stock_analysis()

    # ======================================================
    # CHARGER COMMANDE
    # ======================================================

    def load_order(self):

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                date,
                customer_date,
                po,
                product,
                quantity,
                length,
                upc,
                customer,
                status,
                verification_1,
                verification_2
            FROM orders
            WHERE id = ?
        """, (
            self.order_id,
        ))

        order = cursor.fetchone()

        connection.close()

        if not order:

            QMessageBox.warning(
                self,
                "Erreur",
                "Commande introuvable."
            )

            self.close()
            return

        (
            order_date,
            customer_date,
            po,
            product,
            quantity,
            length,
            upc,
            customer,
            status,
            verification_1,
            verification_2
        ) = order

        self.product = product
        self.quantity = quantity

        self.date_label.setText(
            str(order_date or "")
        )

        self.customer_date_label.setText(
            str(customer_date or "")
        )

        self.po_label.setText(
            str(po or "")
        )

        self.product_label.setText(
            str(product or "")
        )

        self.quantity_label.setText(
            str(quantity or "")
        )

        self.length_label.setText(
            str(length or "")
        )

        self.upc_label.setText(
            str(upc or "")
        )

        self.customer_label.setText(
            str(customer or "")
        )

        self.status_label.setText(
            str(status or "")
        )

        if verification_1:

            self.verification_1_label.setText(
                "✅ Vérification 1 : validée"
            )

        else:

            self.verification_1_label.setText(
                "⏳ Vérification 1 : en attente"
            )

        if verification_2:

            self.verification_2_label.setText(
                "✅ Vérification 2 : validée"
            )

        else:

            self.verification_2_label.setText(
                "⏳ Vérification 2 : en attente"
            )

    # ======================================================
    # HISTORIQUE
    # ======================================================

    def load_history(self):

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                date,
                po,
                quantity,
                length,
                upc
            FROM orders
            WHERE product = ?
              AND id != ?
            ORDER BY id DESC
            LIMIT 10
        """, (
            self.product,
            self.order_id
        ))

        rows = cursor.fetchall()

        connection.close()

        self.history_table.setRowCount(
            len(rows)
        )

        for row_index, row_data in enumerate(rows):

            for column_index, value in enumerate(row_data):

                if value is None:
                    value = ""

                self.history_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(
                        str(value)
                    )
                )

    # ======================================================
    # ANALYSE STOCK
    # ======================================================

    def load_stock_analysis(self):

        try:

            result = analyze_rj45_stock(
                blog_path=BLOG_PATH,
                product_code=self.product,
                requested_qty=self.quantity
            )

        except Exception as exc:

            self.stock_status_label.setText(
                f"❌ Erreur analyse : {exc}"
            )

            return

        # Produit inconnu
        if not result.get("found"):

            self.stock_status_label.setText(
                "⚠ Produit introuvable dans l'historique"
            )

            return

        global_status = result.get(
            "status"
        )

        if global_status == "SUFFICIENT":

            self.stock_status_label.setText(
                "✅ STOCK SUFFISANT"
            )

        elif global_status == "INSUFFICIENT":

            self.stock_status_label.setText(
                "❌ STOCK INSUFFISANT"
            )

        else:

            self.stock_status_label.setText(
                "⚠ STOCK À VÉRIFIER"
            )

        components = result.get(
            "components",
            []
        )

        self.stock_table.setRowCount(
            len(components)
        )

        for row_index, component in enumerate(
            components
        ):

            # Nettoyer les retours ligne dans les noms
            component_name = (
                str(component["component"])
                .replace("\n", " ")
                .strip()
            )

            status = component["status"]

            if status == "SUFFICIENT":
                display_status = "✅ Suffisant"

            elif status == "INSUFFICIENT":
                display_status = "❌ Insuffisant"

            else:
                display_status = "⚠ Inconnu"

            values = [
                component_name,
                component["consumption_per_unit"],
                component["current_stock"],
                component["required_qty"],
                component["projected_stock"],
                display_status
            ]

            for column_index, value in enumerate(
                values
            ):

                if value is None:
                    value = ""

                self.stock_table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(
                        str(value)
                    )
                )