from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox
)

from app.services.dashboard_service import (
    get_dashboard_data
)
from app.ui.background_task import BackgroundTask


class DashboardPage(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            5,
            5,
            5,
            5
        )

        main_layout.setSpacing(
            18
        )

        # ==================================================
        # TITRE
        # ==================================================

        top_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel(
            "Dashboard"
        )

        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #1c293b;
        """)

        subtitle = QLabel(
            "Vue globale des commandes et du stock"
        )

        subtitle.setStyleSheet("""
            color: #7b8798;
            font-size: 10pt;
        """)

        title_layout.addWidget(
            title
        )

        title_layout.addWidget(
            subtitle
        )

        top_layout.addLayout(
            title_layout
        )

        top_layout.addStretch()

        self.refresh_button = QPushButton(
            "Actualiser"
        )

        self.refresh_button.setMinimumHeight(
            40
        )

        self.refresh_button.clicked.connect(
            self.refresh_data
        )

        top_layout.addWidget(self.refresh_button)

        main_layout.addLayout(
            top_layout
        )

        # ==================================================
        # KPI COMMANDES
        # ==================================================

        cards_layout = QHBoxLayout()

        self.total_card = self.create_card(
            "Commandes",
            "0",
            "Total enregistré"
        )

        self.verification1_card = self.create_card(
            "Vérification 1",
            "0",
            "Validées"
        )

        self.verification2_card = self.create_card(
            "Vérification 2",
            "0",
            "À traiter"
        )

        self.erp_card = self.create_card(
            "ERP",
            "0",
            "Prêtes à envoyer"
        )

        cards_layout.addWidget(
            self.total_card["frame"]
        )

        cards_layout.addWidget(
            self.verification1_card["frame"]
        )

        cards_layout.addWidget(
            self.verification2_card["frame"]
        )

        cards_layout.addWidget(
            self.erp_card["frame"]
        )

        main_layout.addLayout(
            cards_layout
        )

        # ==================================================
        # STOCK
        # ==================================================

        stock_frame = QFrame()

        stock_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e4e9f0;
                border-radius: 10px;
            }
        """)

        stock_layout = QVBoxLayout(
            stock_frame
        )

        stock_title = QLabel(
            "État du stock CommScope / RJ45"
        )

        stock_title.setStyleSheet("""
            font-size: 14pt;
            font-weight: bold;
            border: none;
        """)

        stock_layout.addWidget(
            stock_title
        )

        stock_values_layout = QHBoxLayout()

        self.stock_available = QLabel(
            "🟢 Disponible : 0"
        )

        self.stock_low = QLabel(
            "🟠 Stock faible : 0"
        )

        self.stock_rupture = QLabel(
            "🔴 Rupture : 0"
        )

        self.stock_unknown = QLabel(
            "⚠ Inconnu : 0"
        )

        stock_labels = [
            self.stock_available,
            self.stock_low,
            self.stock_rupture,
            self.stock_unknown
        ]

        for label in stock_labels:

            label.setStyleSheet("""
                font-size: 11pt;
                font-weight: 600;
                border: none;
                padding: 8px;
            """)

            stock_values_layout.addWidget(
                label
            )

        stock_values_layout.addStretch()

        stock_layout.addLayout(
            stock_values_layout
        )

        main_layout.addWidget(
            stock_frame
        )

        # ==================================================
        # DERNIERES COMMANDES
        # ==================================================

        recent_title = QLabel(
            "Dernières commandes"
        )

        recent_title.setStyleSheet("""
            font-size: 15pt;
            font-weight: bold;
            color: #1c293b;
        """)

        main_layout.addWidget(
            recent_title
        )

        self.table = QTableWidget()

        self.table.setColumnCount(
            6
        )

        self.table.setHorizontalHeaderLabels([
            "Date",
            "PO",
            "Client",
            "Produit",
            "Qty",
            "Statut"
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
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Stretch
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents
        )

        main_layout.addWidget(
            self.table,
            1
        )

        self._data_worker = None

    # ======================================================
    # CREER CARTE KPI
    # ======================================================

    def create_card(
        self,
        title,
        value,
        subtitle
    ):

        frame = QFrame()

        frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e4e9f0;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(
            frame
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet("""
            color: #7b8798;
            font-size: 10pt;
            font-weight: 600;
            border: none;
        """)

        value_label = QLabel(
            value
        )

        value_label.setStyleSheet("""
            color: #1557a5;
            font-size: 25pt;
            font-weight: bold;
            border: none;
        """)

        subtitle_label = QLabel(
            subtitle
        )

        subtitle_label.setStyleSheet("""
            color: #98a2b3;
            font-size: 9pt;
            border: none;
        """)

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        layout.addWidget(
            subtitle_label
        )

        return {
            "frame": frame,
            "value": value_label
        }

    # ======================================================
    # ACTUALISER
    # ======================================================

    def refresh_data(self):

        if self._data_worker is not None:
            return

        self.refresh_button.setEnabled(False)
        self.refresh_button.setText("Chargement...")
        self._data_worker = BackgroundTask(
            get_dashboard_data,
            self
        )
        self._data_worker.succeeded.connect(self._on_data_loaded)
        self._data_worker.failed.connect(self._on_data_error)
        self._data_worker.finished.connect(self._on_worker_finished)
        self._data_worker.finished.connect(self._data_worker.deleteLater)
        self._data_worker.start()

    def _on_data_loaded(self, data):
        orders = data["orders"]
        stock = data["stock"]
        recent_orders = data[
            "recent_orders"
        ]

        # ==================================================
        # KPI
        # ==================================================

        self.total_card[
            "value"
        ].setText(
            str(
                orders["total_orders"]
            )
        )

        self.verification1_card[
            "value"
        ].setText(
            str(
                orders["verification_1_ok"]
            )
        )

        self.verification2_card[
            "value"
        ].setText(
            str(
                orders[
                    "verification_2_pending"
                ]
            )
        )

        self.erp_card[
            "value"
        ].setText(
            str(
                orders["ready_erp"]
            )
        )

        # ==================================================
        # STOCK
        # ==================================================

        self.stock_available.setText(
            f"🟢 Disponible : {stock['available']}"
        )

        self.stock_low.setText(
            f"🟠 Stock faible : {stock['low']}"
        )

        self.stock_rupture.setText(
            f"🔴 Rupture : {stock['rupture']}"
        )

        self.stock_unknown.setText(
            f"⚠ Inconnu : {stock['unknown']}"
        )

        # ==================================================
        # DERNIERES COMMANDES
        # ==================================================

        self.table.setRowCount(
            len(
                recent_orders
            )
        )

        for row_index, order in enumerate(
            recent_orders
        ):

            status = self.get_status_text(
                order
            )

            values = [
                order.get("date") or "-",
                order.get("po") or "-",
                order.get("customer") or "-",
                order.get("product") or "-",
                order.get("quantity") or "-",
                status
            ]

            for column_index, value in enumerate(
                values
            ):

                item = QTableWidgetItem(
                    str(
                        value
                    )
                )

                if column_index in [
                    0,
                    1,
                    4,
                    5
                ]:

                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.table.setItem(
                    row_index,
                    column_index,
                    item
                )

    def _on_data_error(self, message):
        QMessageBox.warning(
            self,
            "Dashboard",
            message
        )

    def _on_worker_finished(self):
        self._data_worker = None
        self.refresh_button.setEnabled(True)
        self.refresh_button.setText("Actualiser")

    # ======================================================
    # STATUT LISIBLE
    # ======================================================

    @staticmethod
    def get_status_text(order):

        verification_1 = order.get(
            "verification_1"
        )

        verification_2 = order.get(
            "verification_2"
        )

        status = order.get(
            "status"
        )

        if status == "HISTORIQUE":

            return "Historique"

        if status == "READY_ERP":

            return "✅ Prêt ERP"

        if (
            verification_1 == 1
            and verification_2 == 0
        ):

            return "🟠 Vérification 2"

        if verification_1 == 0:

            return "🔵 Vérification 1"

        if verification_2 == 1:

            return "✅ Validée"

        return str(
            status or "-"
        )