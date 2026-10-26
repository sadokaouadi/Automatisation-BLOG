from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QGroupBox,
    QFormLayout,
    QMessageBox
)

from app.services.order_intake_service import (
    prepare_order_from_pdf
)

from app.services.order_service import (
    save_verified_order
)


class NewOrdersPage(QWidget):

    def __init__(self):
        super().__init__()

        # Commande actuellement affichée
        self.current_order = None
        self.current_pdf = None

        # Commandes Outlook arrivées pendant qu'une
        # autre commande est en cours de vérification
        self.pending_orders = []

        main_layout = QVBoxLayout(self)

        # ==================================================
        # TITRE
        # ==================================================

        title = QLabel(
            "NOUVELLES COMMANDES"
        )

        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            margin-bottom: 15px;
        """)

        main_layout.addWidget(title)

        # ==================================================
        # INFORMATION FILE D'ATTENTE
        # ==================================================

        self.pending_label = QLabel(
            "Aucune commande Outlook en attente"
        )

        self.pending_label.setStyleSheet("""
            padding: 5px;
            font-weight: bold;
        """)

        main_layout.addWidget(
            self.pending_label
        )

        # ==================================================
        # IMPORT MANUEL PDF
        # ==================================================

        top_layout = QHBoxLayout()

        self.import_button = QPushButton(
            "📄 Choisir un PDF"
        )

        self.import_button.setMinimumHeight(
            45
        )

        self.import_button.clicked.connect(
            self.select_pdf
        )

        self.pdf_label = QLabel(
            "Aucun PDF sélectionné"
        )

        top_layout.addWidget(
            self.import_button
        )

        top_layout.addWidget(
            self.pdf_label,
            1
        )

        main_layout.addLayout(
            top_layout
        )

        # ==================================================
        # INFORMATIONS EXTRAITES
        # ==================================================

        order_group = QGroupBox(
            "Vérification 1 — Données extraites"
        )

        form = QFormLayout(
            order_group
        )

        self.customer_label = QLabel("-")
        self.po_label = QLabel("-")
        self.po_date_label = QLabel("-")
        self.delivery_date_label = QLabel("-")
        self.product_label = QLabel("-")
        self.quantity_label = QLabel("-")
        self.mt_label = QLabel("-")
        self.upc_label = QLabel("-")
        self.source_label = QLabel("-")

        form.addRow(
            "Client :",
            self.customer_label
        )

        form.addRow(
            "PO :",
            self.po_label
        )

        form.addRow(
            "PO Date :",
            self.po_date_label
        )

        form.addRow(
            "Delivery Date :",
            self.delivery_date_label
        )

        form.addRow(
            "Produit :",
            self.product_label
        )

        form.addRow(
            "Quantité :",
            self.quantity_label
        )

        form.addRow(
            "mt :",
            self.mt_label
        )

        form.addRow(
            "UPC :",
            self.upc_label
        )

        form.addRow(
            "Extraction :",
            self.source_label
        )

        main_layout.addWidget(
            order_group
        )

        # ==================================================
        # ALERTES / WARNINGS
        # ==================================================

        self.warning_label = QLabel()

        self.warning_label.setWordWrap(
            True
        )

        self.warning_label.setStyleSheet("""
            padding: 10px;
            font-weight: bold;
        """)

        main_layout.addWidget(
            self.warning_label
        )

        # ==================================================
        # ACTIONS
        # ==================================================

        actions = QHBoxLayout()

        self.open_pdf_button = QPushButton(
            "👁 Ouvrir PDF"
        )

        self.reject_button = QPushButton(
            "❌ Rejeter"
        )

        self.validate_button = QPushButton(
            "✅ Valider Vérification 1"
        )

        for button in [
            self.open_pdf_button,
            self.reject_button,
            self.validate_button
        ]:
            button.setMinimumHeight(
                45
            )

        self.open_pdf_button.clicked.connect(
            self.open_pdf
        )

        self.reject_button.clicked.connect(
            self.reject_order
        )

        self.validate_button.clicked.connect(
            self.validate_order
        )

        # Aucun PDF au démarrage
        self.open_pdf_button.setEnabled(
            False
        )

        self.reject_button.setEnabled(
            False
        )

        self.validate_button.setEnabled(
            False
        )

        actions.addWidget(
            self.open_pdf_button
        )

        actions.addStretch()

        actions.addWidget(
            self.reject_button
        )

        actions.addWidget(
            self.validate_button
        )

        main_layout.addLayout(
            actions
        )

        main_layout.addStretch()

    # ======================================================
    # CHOISIR PDF MANUELLEMENT
    # ======================================================

    def select_pdf(self):

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir une commande PDF",
            "data/uploads",
            "PDF (*.pdf *.PDF)"
        )

        if not filepath:
            return

        self.load_pdf(
            filepath
        )

    # ======================================================
    # EXTRACTION MANUELLE DU PDF
    # ======================================================

    def load_pdf(self, filepath):

        try:

            result = prepare_order_from_pdf(
                filepath
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Erreur extraction PDF",
                str(exc)
            )

            return

        self.load_prepared_order(
            result
        )

    # ======================================================
    # AFFICHER UNE COMMANDE DEJA PREPAREE
    # Manuel OU Outlook
    # ======================================================

    def load_prepared_order(
        self,
        result
    ):

        self.current_order = result

        self.current_pdf = result.get(
            "pdf_path"
        )

        # --------------------------------------------------
        # PDF
        # --------------------------------------------------

        if self.current_pdf:

            self.pdf_label.setText(
                Path(
                    self.current_pdf
                ).name
            )

        else:

            self.pdf_label.setText(
                "PDF non disponible"
            )

        # --------------------------------------------------
        # INFORMATIONS
        # --------------------------------------------------

        self.customer_label.setText(
            str(
                result.get(
                    "customer"
                )
                or ""
            )
        )

        self.po_label.setText(
            str(
                result.get(
                    "po_number"
                )
                or ""
            )
        )

        self.po_date_label.setText(
            str(
                result.get(
                    "po_date"
                )
                or ""
            )
        )

        self.delivery_date_label.setText(
            str(
                result.get(
                    "delivery_date"
                )
                or ""
            )
        )

        self.product_label.setText(
            str(
                result.get(
                    "product"
                )
                or ""
            )
        )

        self.quantity_label.setText(
            str(
                result.get(
                    "quantity"
                )
                or ""
            )
        )

        self.mt_label.setText(
            str(
                result.get(
                    "mt"
                )
                or ""
            )
        )

        self.upc_label.setText(
            str(
                result.get(
                    "upc"
                )
                or ""
            )
        )

        self.source_label.setText(
            str(
                result.get(
                    "extraction_source"
                )
                or ""
            )
        )

        # --------------------------------------------------
        # WARNINGS
        # --------------------------------------------------

        warnings = result.get(
            "warnings",
            []
        )

        if warnings:

            self.warning_label.setText(
                "⚠ "
                + "\n⚠ ".join(
                    warnings
                )
            )

            self.warning_label.setStyleSheet("""
                padding: 10px;
                font-weight: bold;
            """)

        else:

            self.warning_label.setText(
                "✅ Aucune anomalie détectée"
            )

        # --------------------------------------------------
        # BOUTONS
        # --------------------------------------------------

        self.open_pdf_button.setEnabled(
            bool(
                self.current_pdf
            )
        )

        self.reject_button.setEnabled(
            True
        )

        self.validate_button.setEnabled(
            result.get(
                "ready",
                False
            )
        )

        self.update_pending_label()

    # ======================================================
    # RECEPTION AUTOMATIQUE OUTLOOK
    # ======================================================

    def receive_outlook_order(
        self,
        order
    ):

        # Aucune commande actuellement affichée :
        # afficher directement la nouvelle commande.
        if self.current_order is None:

            self.load_prepared_order(
                order
            )

            return

        # Une commande est déjà en vérification.
        # Garder la nouvelle dans la file d'attente.
        self.pending_orders.append(
            order
        )

        self.update_pending_label()

    # ======================================================
    # AFFICHER NOMBRE DE COMMANDES EN ATTENTE
    # ======================================================

    def update_pending_label(self):

        count = len(
            self.pending_orders
        )

        if count == 0:

            self.pending_label.setText(
                "Aucune commande Outlook en attente"
            )

        elif count == 1:

            self.pending_label.setText(
                "🔔 1 commande Outlook en attente"
            )

        else:

            self.pending_label.setText(
                f"🔔 {count} commandes Outlook en attente"
            )

    # ======================================================
    # OUVRIR PDF
    # ======================================================

    def open_pdf(self):

        if not self.current_pdf:
            return

        pdf_path = Path(
            self.current_pdf
        ).resolve()

        if not pdf_path.exists():

            QMessageBox.warning(
                self,
                "PDF",
                "Le fichier PDF est introuvable."
            )

            return

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                str(
                    pdf_path
                )
            )
        )

    # ======================================================
    # VALIDER VERIFICATION 1
    # ======================================================

    def validate_order(self):

        if not self.current_order:
            return

        po_number = (
            self.current_order.get(
                "po_number",
                ""
            )
        )

        product = (
            self.current_order.get(
                "product",
                ""
            )
        )

        quantity = (
            self.current_order.get(
                "quantity",
                ""
            )
        )

        answer = QMessageBox.question(
            self,
            "Validation",
            (
                "Confirmer la première vérification ?\n\n"
                f"PO : {po_number}\n"
                f"Produit : {product}\n"
                f"Quantité : {quantity}"
            ),
            (
                QMessageBox.StandardButton.Yes
                |
                QMessageBox.StandardButton.No
            )
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        result = save_verified_order(
            self.current_order
        )

        if not result[
            "success"
        ]:

            QMessageBox.warning(
                self,
                "Commande",
                result["message"]
            )

            return

        QMessageBox.information(
            self,
            "Commande validée",
            (
                "✅ Vérification 1 validée.\n\n"
                "La commande est maintenant prête "
                "pour la Vérification 2."
            )
        )

        self.clear_order()

    # ======================================================
    # REJETER
    # ======================================================

    def reject_order(self):

        if not self.current_order:
            return

        answer = QMessageBox.question(
            self,
            "Rejeter la commande",
            (
                "Confirmer le rejet de cette "
                "commande ?"
            ),
            (
                QMessageBox.StandardButton.Yes
                |
                QMessageBox.StandardButton.No
            )
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        self.clear_order()

    # ======================================================
    # EFFACER LA COMMANDE ACTUELLE
    # ======================================================

    def clear_order(self):

        self.current_order = None
        self.current_pdf = None

        self.pdf_label.setText(
            "Aucun PDF sélectionné"
        )

        for label in [
            self.customer_label,
            self.po_label,
            self.po_date_label,
            self.delivery_date_label,
            self.product_label,
            self.quantity_label,
            self.mt_label,
            self.upc_label,
            self.source_label
        ]:

            label.setText(
                "-"
            )

        self.warning_label.clear()

        self.open_pdf_button.setEnabled(
            False
        )

        self.reject_button.setEnabled(
            False
        )

        self.validate_button.setEnabled(
            False
        )

        # --------------------------------------------------
        # COMMANDES OUTLOOK EN ATTENTE
        # --------------------------------------------------

        if self.pending_orders:

            next_order = (
                self.pending_orders.pop(
                    0
                )
            )

            self.load_prepared_order(
                next_order
            )

        else:

            self.update_pending_label()