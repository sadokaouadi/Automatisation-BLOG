import io
import os
import re
import shutil
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image
from pypdf import PdfReader


# =========================================================
# CONFIGURATION TESSERACT
# =========================================================

TESSERACT_CANDIDATES = [
    os.environ.get("TESSERACT_CMD"),
    shutil.which("tesseract"),
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


def configure_tesseract():
    """
    Cherche automatiquement Tesseract.

    Sur ton PC, le chemin attendu est :
    C:\\Program Files\\Tesseract-OCR\\tesseract.exe
    """

    for candidate in TESSERACT_CANDIDATES:
        if not candidate:
            continue

        candidate_path = Path(candidate)

        if candidate_path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate_path)
            return str(candidate_path)

    return None


# Configuration immédiate au chargement du module.
TESSERACT_PATH = configure_tesseract()


# =========================================================
# CONSTANTES / REGEX
# =========================================================

MONTHS = {
    "JAN": "Jan",
    "FEB": "Feb",
    "MAR": "Mar",
    "APR": "Apr",
    "MAY": "May",
    "JUN": "Jun",
    "JUL": "Jul",
    "AUG": "Aug",
    "SEP": "Sep",
    "OCT": "Oct",
    "NOV": "Nov",
    "DEC": "Dec",
}

DATE_RE = (
    r"(\d{1,2}[\s\-/]+"
    r"(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
    r"[A-Z]*[\s\-/]+\d{2,4})"
)


# =========================================================
# OUTILS TEXTE
# =========================================================

def clean_text(text):
    """
    Nettoie les espaces sans détruire la structure des lignes.
    """

    if not text:
        return ""

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = text.replace("\xa0", " ")

    cleaned_lines = []

    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()

        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def compact_text(text):
    """
    Version du texte sur une seule ligne.
    Utile pour les regex qui doivent traverser
    les retours à la ligne du PDF.
    """

    return re.sub(r"\s+", " ", text or "").strip()


def normalize_product(value):
    """
    Supprime les espaces parasites dans les références produit.
    """

    if not value:
        return ""

    value = re.sub(r"\s+", "", value)

    return value.upper().strip()


# =========================================================
# EXTRACTION TEXTE NATIVE PYPDF
# =========================================================

def read_pdf_text_native(pdf_path):
    """
    Essaie deux modes pypdf :
    - extraction normale
    - extraction layout

    Le meilleur résultat est conservé pour chaque page.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF introuvable : {pdf_path}"
        )

    reader = PdfReader(str(pdf_path))
    pages_text = []

    for page in reader.pages:

        normal_text = ""
        layout_text = ""

        try:
            normal_text = page.extract_text() or ""
        except Exception:
            normal_text = ""

        try:
            layout_text = (
                page.extract_text(
                    extraction_mode="layout"
                )
                or ""
            )
        except Exception:
            layout_text = ""

        # On garde la version qui semble la plus utile.
        candidates = [
            normal_text,
            layout_text,
        ]

        best_text = max(
            candidates,
            key=lambda value: len(
                (value or "").strip()
            ),
        )

        pages_text.append(best_text)

    return clean_text(
        "\n".join(pages_text)
    )


# =========================================================
# OCR TESSERACT
# =========================================================

def ocr_pdf_pages(
    pdf_path,
    max_pages=2,
    zoom=3.0,
):
    """
    OCR de secours pour les PDF scannés / image.

    On OCR uniquement les premières pages.
    Pour les PO CommScope, les informations importantes
    sont normalement sur la page 1.
    """

    if not TESSERACT_PATH:
        raise RuntimeError(
            "Tesseract OCR est introuvable. "
            "Installez Tesseract ou définissez "
            "la variable TESSERACT_CMD."
        )

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF introuvable : {pdf_path}"
        )

    document = pymupdf.open(str(pdf_path))

    try:

        pages_to_read = min(
            len(document),
            max_pages,
        )

        ocr_pages = []

        matrix = pymupdf.Matrix(
            zoom,
            zoom,
        )

        for page_index in range(
            pages_to_read
        ):

            page = document[
                page_index
            ]

            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False,
            )

            image_bytes = (
                pixmap.tobytes("png")
            )

            image = Image.open(
                io.BytesIO(
                    image_bytes
                )
            )

            # Anglais suffit pour les PO CommScope.
            # psm 6 donne de bons résultats sur
            # une page structurée type bon de commande.
            page_text = (
                pytesseract.image_to_string(
                    image,
                    lang="eng",
                    config="--oem 3 --psm 6",
                )
                or ""
            )

            ocr_pages.append(
                page_text
            )

        return clean_text(
            "\n".join(ocr_pages)
        )

    finally:
        document.close()


# =========================================================
# SCORE DE QUALITÉ DU TEXTE
# =========================================================

def extraction_signal_score(
    text,
    pdf_path=None,
):
    """
    Mesure si le texte contient les informations
    utiles pour une commande CommScope.

    Le score permet de décider si OCR est nécessaire.
    """

    if not text:
        return 0

    compact = compact_text(text)
    upper = compact.upper()

    score = 0

    if "COMMSCOPE" in upper:
        score += 2

    if re.search(
        r"\b8\d{9}\b",
        compact,
    ):
        score += 3

    if re.search(
        DATE_RE,
        compact,
        re.IGNORECASE,
    ):
        score += 1

    if re.search(
        r"DELIVERY\s+DATE",
        compact,
        re.IGNORECASE,
    ):
        score += 1

    if re.search(
        r"\bNPC[A-Z0-9]*\s*-\s*[A-Z0-9]+\b",
        compact,
        re.IGNORECASE,
    ):
        score += 4

    if re.search(
        r"\b(?:EACH|EA|PCS?)\b",
        compact,
        re.IGNORECASE,
    ):
        score += 1

    # Le nom du fichier peut contenir le PO.
    if pdf_path is not None:

        filename = Path(
            pdf_path
        ).stem

        if re.search(
            r"\b8\d{9}\b",
            filename,
        ):
            score += 1

    return score


def read_pdf_text(pdf_path):
    """
    Stratégie finale :

    1. Essayer pypdf.
    2. Si le texte n'est pas assez exploitable,
       lancer OCR sur les premières pages.
    3. Garder la version ayant le meilleur score.
    """

    native_text = (
        read_pdf_text_native(
            pdf_path
        )
    )

    native_score = (
        extraction_signal_score(
            native_text,
            pdf_path,
        )
    )

    # Cas normal :
    # suffisamment de signaux pour éviter OCR.
    if (
        len(native_text.strip()) >= 80
        and native_score >= 7
    ):
        return {
            "text": native_text,
            "source": "PYPDF",
            "native_score": native_score,
            "ocr_score": None,
        }

    # Sinon OCR de secours.
    try:

        ocr_text = ocr_pdf_pages(
            pdf_path,
            max_pages=2,
        )

        ocr_score = (
            extraction_signal_score(
                ocr_text,
                pdf_path,
            )
        )

        if ocr_score >= native_score:

            return {
                "text": ocr_text,
                "source": "OCR",
                "native_score": native_score,
                "ocr_score": ocr_score,
            }

    except Exception as exc:

        # On garde pypdf si OCR échoue.
        return {
            "text": native_text,
            "source": "PYPDF_OCR_FAILED",
            "native_score": native_score,
            "ocr_score": None,
            "ocr_error": str(exc),
        }

    return {
        "text": native_text,
        "source": "PYPDF",
        "native_score": native_score,
        "ocr_score": ocr_score,
    }


# =========================================================
# DÉTECTION CLIENT
# =========================================================

def detect_customer(text):

    upper = (
        text or ""
    ).upper()

    if "COMMSCOPE" in upper:
        return "CommScope"

    if "TE CONNECTIVITY" in upper:
        return "TE Connectivity"

    if (
        "AMPHENOL" in upper
        or "SOCAPEX" in upper
    ):
        return "Amphenol Socapex"

    return "Unknown"


# =========================================================
# NUMÉRO DE PO
# =========================================================

def extract_po_number(
    text,
    pdf_path=None,
):
    """
    Cherche dans le contenu puis utilise
    le nom du PDF comme dernier fallback.
    """

    compact = compact_text(text)

    patterns = [
        (
            r"Purchase\s+Order\s*"
            r"(?:No\.?|Number)?\s*[:#]?\s*"
            r"(8\d{9})"
        ),
        (
            r"PO\s*(?:No\.?|Number)?\s*"
            r"[:#]?\s*(8\d{9})"
        ),
        r"\b(800\d{7})\b",
        r"\b(8\d{9})\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            compact,
            re.IGNORECASE,
        )

        if match:
            return match.group(1)

    # Dernier secours :
    # numéro présent dans le nom du PDF.
    if pdf_path is not None:

        filename = Path(
            pdf_path
        ).stem

        match = re.search(
            r"\b(8\d{9})\b",
            filename,
        )

        if match:
            return match.group(1)

    return ""


# =========================================================
# DATES
# =========================================================

def normalize_date(
    date_text,
):

    if not date_text:
        return ""

    date_text = re.sub(
        r"[\-/]+",
        " ",
        date_text.strip(),
    )

    parts = (
        date_text.split()
    )

    if len(parts) != 3:
        return date_text

    day, month, year = parts

    month_key = (
        month[:3].upper()
    )

    month = MONTHS.get(
        month_key,
        month.title(),
    )

    if len(year) == 2:
        year = f"20{year}"

    try:
        day = str(
            int(day)
        ).zfill(2)
    except ValueError:
        pass

    return (
        f"{day}-{month}-{year}"
    )


def find_all_dates(
    text,
):

    dates = re.findall(
        DATE_RE,
        text or "",
        re.IGNORECASE,
    )

    result = []

    for date_value in dates:

        normalized = (
            normalize_date(
                date_value
            )
        )

        if normalized not in result:
            result.append(
                normalized
            )

    return result


def extract_dates(
    text,
    po_number="",
):

    compact = compact_text(
        text
    )

    po_date = ""
    delivery_date = ""

    # -----------------------------------------------------
    # DATE DE LIVRAISON
    # -----------------------------------------------------

    delivery_patterns = [
        (
            rf"Delivery\s+date\s*:?\s*"
            rf"{DATE_RE}"
        ),
        (
            rf"Requested\s+"
            rf"(?:delivery\s+)?date\s*:?\s*"
            rf"{DATE_RE}"
        ),
        (
            rf"Customer\s+date\s*:?\s*"
            rf"{DATE_RE}"
        ),
    ]

    for pattern in delivery_patterns:

        match = re.search(
            pattern,
            compact,
            re.IGNORECASE,
        )

        if match:

            delivery_date = (
                normalize_date(
                    match.group(1)
                )
            )

            break

    # -----------------------------------------------------
    # DATE DU PO
    # -----------------------------------------------------

    po_patterns = []

    if po_number:

        escaped_po = re.escape(
            po_number
        )

        # Structure fréquente :
        # PO Date:
        # 8005017064
        # 07 MAY 2026
        po_patterns.append(
            (
                rf"PO\s+Date\s*:?\s*"
                rf"{escaped_po}\s*"
                rf"{DATE_RE}"
            )
        )

        # Fallback numéro PO + date.
        po_patterns.append(
            (
                rf"{escaped_po}\s*"
                rf"{DATE_RE}"
            )
        )

    po_patterns.extend([
        (
            rf"PO\s+Date\s*:?\s*"
            rf"{DATE_RE}"
        ),
        (
            rf"Order\s+Date\s*:?\s*"
            rf"{DATE_RE}"
        ),
    ])

    for pattern in po_patterns:

        match = re.search(
            pattern,
            compact,
            re.IGNORECASE,
        )

        if match:

            po_date = (
                normalize_date(
                    match.group(1)
                )
            )

            break

    # -----------------------------------------------------
    # FALLBACK CHRONOLOGIQUE
    # -----------------------------------------------------

    all_dates = find_all_dates(
        text
    )

    if (
        not po_date
        and all_dates
    ):
        po_date = all_dates[0]

    if not delivery_date:

        if len(all_dates) >= 2:
            delivery_date = (
                all_dates[1]
            )

        elif all_dates:
            delivery_date = (
                all_dates[0]
            )

    return (
        po_date,
        delivery_date,
    )


# =========================================================
# PRODUIT
# =========================================================

def extract_product(
    text,
):

    compact = compact_text(
        text
    )

    patterns = [
        (
            r"\b("
            r"NPC[A-Z0-9]*\s*-\s*[A-Z0-9]+"
            r")\b"
        ),
        (
            r"\b("
            r"NPP[A-Z0-9]*\s*-\s*[A-Z0-9]+"
            r")\b"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            compact,
            re.IGNORECASE,
        )

        if match:

            return normalize_product(
                match.group(1)
            )

    # Fallback générique.
    generic = re.search(
        (
            r"\b("
            r"[A-Z0-9]{3,}"
            r"[A-Z0-9\-]*"
            r"-"
            r"[A-Z0-9\-]{3,}"
            r")\b"
        ),
        compact,
        re.IGNORECASE,
    )

    if generic:

        candidate = (
            normalize_product(
                generic.group(1)
            )
        )

        if len(candidate) >= 8:
            return candidate

    return ""


# =========================================================
# QUANTITÉ
# =========================================================

def normalize_ocr_number_token(value):
    """
    Corrige les confusions OCR fréquentes dans un nombre.

    Exemples :
    - 2OO -> 200
    - 2O0 -> 200
    - l00 -> 100
    - I00 -> 100
    """

    if value is None:
        return ""

    value = str(value).strip()

    replacements = {
        "O": "0",
        "o": "0",
        "Q": "0",
        "I": "1",
        "l": "1",
        "|": "1",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    # Pour une quantité, les séparateurs de milliers sont supprimés.
    value = value.replace(",", "")
    value = value.replace(" ", "")

    # On accepte uniquement un entier après normalisation.
    if not re.fullmatch(r"\d+", value):
        return ""

    return value


def parse_positive_int(value):
    """
    Convertit une valeur en entier positif,
    avec correction des erreurs OCR fréquentes.
    """

    normalized = normalize_ocr_number_token(value)

    if not normalized:
        return 0

    try:
        quantity = int(normalized)

        if quantity > 0:
            return quantity

    except ValueError:
        pass

    return 0


def extract_qty_from_product_context(context):
    """
    Extrait la quantité située entre la référence produit
    et l'unité de mesure.

    Exemple :
        NPC6AUZDB-RD001M A 2OO Each

    Retourne 200 même si Tesseract lit 2OO.
    """

    if not context:
        return 0

    # On s'arrête à l'unité de mesure.
    uom_match = re.search(
        r"\b(?:Each|EA|PC|PCS)\b",
        context,
        re.IGNORECASE,
    )

    if not uom_match:
        return 0

    before_uom = context[:uom_match.start()].strip()

    # On cherche les tokens numériques possibles.
    # O/I/l sont inclus car OCR peut les confondre avec 0/1.
    candidates = re.findall(
        r"\b[0-9OoQIl|][0-9OoQIl|,]*\b",
        before_uom,
    )

    # La quantité est normalement le dernier nombre
    # entre la référence produit et "Each".
    for candidate in reversed(candidates):
        quantity = parse_positive_int(candidate)

        if quantity > 0:
            return quantity

    return 0


def extract_quantity(
    text,
    product,
):
    """
    Extraction robuste de la quantité CommScope.

    Gère notamment :
    - 200
    - 2,400
    - erreurs OCR comme 2OO / 2O0
    - cas où Tesseract ne lit pas l'unité "Each"

    Exemple OCR réel :
        00010 NPC6AUZDB-RD001M A 200
    """

    if not product:
        return 0

    normalized_product = normalize_product(product)

    # -----------------------------------------------------
    # 1. RECHERCHE LIGNE PAR LIGNE
    # -----------------------------------------------------

    for line in (text or "").splitlines():

        compact_line = compact_text(line)
        normalized_line = normalize_product(compact_line)

        if normalized_product not in normalized_line:
            continue

        # -------------------------------------------------
        # A. Format normal avec unité
        # Ex:
        # NPC6ASZDB-WT002M A 2,400 Each
        # -------------------------------------------------

        qty_patterns = [
            (
                r"\b[A-Z]\s+"
                r"([0-9OoQIl|,]+)\s+"
                r"(?:Each|EA|PC|PCS)\b"
            ),
            (
                r"\b([0-9OoQIl|,]+)\s+"
                r"(?:Each|EA|PC|PCS)\b"
            ),
        ]

        for pattern in qty_patterns:

            match = re.search(
                pattern,
                compact_line,
                re.IGNORECASE,
            )

            if match:

                quantity = parse_positive_int(
                    match.group(1)
                )

                if quantity:
                    return quantity

        # -------------------------------------------------
        # B. FORMAT OCR SANS "Each"
        #
        # Cas réel rencontré :
        # 00010 NPC6AUZDB-RD001M A 200
        #
        # On cherche donc :
        # produit + révision éventuelle + quantité
        # -------------------------------------------------

        product_pattern = re.escape(product).replace(
            r"\-",
            r"\s*-\s*"
        )

        no_uom_patterns = [
            (
                rf"{product_pattern}\s+"
                rf"[A-Z]\s+"
                rf"([0-9OoQIl|,]+)"
                rf"(?:\s|$)"
            ),
            (
                rf"{product_pattern}\s+"
                rf"([0-9OoQIl|,]+)"
                rf"(?:\s|$)"
            ),
        ]

        for pattern in no_uom_patterns:

            match = re.search(
                pattern,
                compact_line,
                re.IGNORECASE,
            )

            if match:

                quantity = parse_positive_int(
                    match.group(1)
                )

                if quantity:
                    return quantity

        # -------------------------------------------------
        # C. Fallback contextuel
        # -------------------------------------------------

        product_match = re.search(
            product_pattern,
            compact_line,
            re.IGNORECASE,
        )

        if product_match:

            after_product = compact_line[
                product_match.end():
            ].strip()

            # Supprimer une éventuelle lettre de révision
            # située juste après le produit.
            after_product = re.sub(
                r"^[A-Z]\s+",
                "",
                after_product,
                count=1,
                flags=re.IGNORECASE,
            )

            # Prendre le premier token ressemblant
            # à un nombre après le produit.
            candidate_match = re.match(
                r"([0-9OoQIl|,]+)",
                after_product,
            )

            if candidate_match:

                quantity = parse_positive_int(
                    candidate_match.group(1)
                )

                if quantity:
                    return quantity

    # -----------------------------------------------------
    # 2. RECHERCHE DANS LE TEXTE COMPLET
    # -----------------------------------------------------

    compact = compact_text(text)

    product_pattern = re.escape(product).replace(
        r"\-",
        r"\s*-\s*"
    )

    # Avec unité
    patterns = [
        (
            rf"{product_pattern}\s+"
            rf"[A-Z]\s+"
            rf"([0-9OoQIl|,]+)\s+"
            rf"(?:Each|EA|PC|PCS)\b"
        ),
        (
            rf"{product_pattern}\s+"
            rf"([0-9OoQIl|,]+)\s+"
            rf"(?:Each|EA|PC|PCS)\b"
        ),
        # Sans unité : fallback OCR
        (
            rf"{product_pattern}\s+"
            rf"[A-Z]\s+"
            rf"([0-9OoQIl|,]+)"
            rf"(?:\s|$)"
        ),
        (
            rf"{product_pattern}\s+"
            rf"([0-9OoQIl|,]+)"
            rf"(?:\s|$)"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            compact,
            re.IGNORECASE,
        )

        if match:

            quantity = parse_positive_int(
                match.group(1)
            )

            if quantity:
                return quantity

    return 0


# =========================================================
# WARNINGS
# =========================================================

def build_warnings(
    customer,
    po_number,
    po_date,
    delivery_date,
    product,
    quantity,
    text,
    extraction_source,
):

    warnings = []

    if not (
        text or ""
    ).strip():

        warnings.append(
            "Aucun texte exploitable "
            "n'a été extrait du PDF."
        )

    if customer == "Unknown":

        warnings.append(
            "Client non identifié automatiquement."
        )

    if not po_number:

        warnings.append(
            "Numéro de PO non détecté."
        )

    if not po_date:

        warnings.append(
            "Date de commande non détectée."
        )

    if not delivery_date:

        warnings.append(
            "Date de livraison non détectée."
        )

    if not product:

        warnings.append(
            "Produit non détecté."
        )

    if not quantity:

        warnings.append(
            "Quantité non détectée."
        )

    if extraction_source == "OCR":

        warnings.append(
            "Texte récupéré par OCR "
            "(PDF image/scanné)."
        )

    return warnings


# =========================================================
# EXTRACTION PRINCIPALE
# =========================================================

def extract_po_from_pdf(
    pdf_path,
):
    """
    Extraction finale utilisée par Streamlit.

    PDF texte :
        pypdf

    PDF image/scanné :
        OCR automatique avec Tesseract
    """

    extraction = (
        read_pdf_text(
            pdf_path
        )
    )

    text = extraction.get(
        "text",
        "",
    )

    extraction_source = (
        extraction.get(
            "source",
            "UNKNOWN",
        )
    )

    customer = (
        detect_customer(
            text
        )
    )

    po_number = (
        extract_po_number(
            text,
            pdf_path=pdf_path,
        )
    )

    (
        po_date,
        delivery_date,
    ) = extract_dates(
        text,
        po_number=po_number,
    )

    product = (
        extract_product(
            text
        )
    )

    quantity = (
        extract_quantity(
            text,
            product,
        )
    )

    warnings = (
        build_warnings(
            customer=customer,
            po_number=po_number,
            po_date=po_date,
            delivery_date=delivery_date,
            product=product,
            quantity=quantity,
            text=text,
            extraction_source=(
                extraction_source
            ),
        )
    )

    lines = []

    # IMPORTANT :
    # on ne crée pas une fausse ligne produit vide.
    if product:

        lines.append({
            "item_code": product,
            "quantity": quantity,
        })

    result = {
        "customer": customer,
        "po_number": po_number,
        "po_date": po_date,
        "delivery_date": delivery_date,
        "lines": lines,
        "warnings": warnings,
        "extraction_source": extraction_source,
        "raw_text_preview": text[:5000],
        "native_score": extraction.get(
            "native_score"
        ),
        "ocr_score": extraction.get(
            "ocr_score"
        ),
    }

    if extraction.get(
        "ocr_error"
    ):

        result["ocr_error"] = (
            extraction[
                "ocr_error"
            ]
        )

    return result


# =========================================================
# TEST DIRECT EN POWERSHELL
# =========================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        print(
            "Usage : "
            "python services\\pdf_po_extractor.py "
            "\"chemin\\vers\\commande.pdf\""
        )

        raise SystemExit(1)

    result = extract_po_from_pdf(
        sys.argv[1]
    )

    print()
    print(
        "================================"
    )
    print(
        "EXTRACTION PDF"
    )
    print(
        "================================"
    )

    print(
        "Source       :",
        result[
            "extraction_source"
        ],
    )

    print(
        "Client       :",
        result[
            "customer"
        ],
    )

    print(
        "PO           :",
        result[
            "po_number"
        ],
    )

    print(
        "PO Date      :",
        result[
            "po_date"
        ],
    )

    print(
        "Delivery Date:",
        result[
            "delivery_date"
        ],
    )

    print(
        "Lines        :",
        result[
            "lines"
        ],
    )

    print(
        "Warnings     :",
        result[
            "warnings"
        ],
    )

    if result.get(
        "ocr_error"
    ):

        print(
            "OCR Error    :",
            result[
                "ocr_error"
            ],
        )
