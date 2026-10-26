from pathlib import Path

from app.services.pdf_po_extractor import extract_po_from_pdf
from app.services.client_router import detect_client

from app.services.clients.commscope.product_lookup import (
    find_product_in_rj45_blog
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

COMMSCOPE_BLOG = (
    PROJECT_ROOT
    / "data"
    / "imports"
    / "BLOG_2026_RJ45.xlsx"
)


def prepare_order_from_pdf(pdf_path):
    """
    Prépare une commande pour la première vérification.

    Cette fonction :
    1. extrait le PDF,
    2. détecte le client,
    3. récupère le produit et la quantité,
    4. enrichit les données avec le BLOG du client,
    5. retourne la commande sans encore l'enregistrer.
    """

    pdf_path = Path(pdf_path)

    # ==========================================
    # 1. EXTRACTION PDF
    # ==========================================

    extraction = extract_po_from_pdf(
        pdf_path
    )

    customer = extraction.get(
        "customer",
        ""
    )

    po_number = extraction.get(
        "po_number",
        ""
    )

    po_date = extraction.get(
        "po_date",
        ""
    )

    delivery_date = extraction.get(
        "delivery_date",
        ""
    )

    warnings = list(
        extraction.get(
            "warnings",
            []
        )
    )

    lines = extraction.get(
        "lines",
        []
    )

    product = ""
    quantity = 0

    if lines:
        product = lines[0].get(
            "item_code",
            ""
        )

        quantity = lines[0].get(
            "quantity",
            0
        )

    # ==========================================
    # 2. ROUTAGE CLIENT
    # ==========================================

    client_info = detect_client(
        customer
    )

    if not client_info["found"]:

        warnings.append(
            f"Client non configuré : {customer}"
        )

        return {
            "ready": False,
            "customer": customer,
            "client_info": client_info,
            "po_number": po_number,
            "po_date": po_date,
            "delivery_date": delivery_date,
            "product": product,
            "quantity": quantity,
            "mt": None,
            "upc": None,
            "warnings": warnings,
            "pdf_path": str(pdf_path),
            "extraction_source":
                extraction.get(
                    "extraction_source"
                )
        }

    # ==========================================
    # 3. DONNEES SPECIFIQUES COMMSCOPE
    # ==========================================

    mt = None
    upc = None

    product_found = False

    if (
        client_info["client_key"]
        == "COMMSCOPE"
        and product
    ):

        lookup = find_product_in_rj45_blog(
            COMMSCOPE_BLOG,
            product
        )

        product_found = lookup.get(
            "found",
            False
        )

        if product_found:

            mt = lookup.get("mt")
            upc = lookup.get("upc")

        else:

            warnings.append(
                "Produit absent du BLOG RJ45."
            )

    # ==========================================
    # 4. RESULTAT POUR VERIFICATION 1
    # ==========================================

    return {
        "ready": True,
        "customer": customer,
        "client_info": client_info,

        "po_number": po_number,
        "po_date": po_date,
        "delivery_date": delivery_date,

        "product": product,
        "quantity": quantity,

        "mt": mt,
        "upc": upc,

        "product_found_in_blog":
            product_found,

        "warnings": warnings,

        "pdf_path": str(pdf_path),

        "extraction_source":
            extraction.get(
                "extraction_source"
            )
    }