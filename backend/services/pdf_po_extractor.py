import re
from pathlib import Path
from pypdf import PdfReader


MONTHS = {
    "JAN": "Jan", "FEB": "Feb", "MAR": "Mar", "APR": "Apr",
    "MAY": "May", "JUN": "Jun", "JUL": "Jul", "AUG": "Aug",
    "SEP": "Sep", "OCT": "Oct", "NOV": "Nov", "DEC": "Dec"
}


def read_pdf_text(pdf_path):
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF introuvable : {pdf_path}")

    reader = PdfReader(str(pdf_path))
    text = ""

    for page in reader.pages:
        page_text = page.extract_text() or ""
        text += "\n" + page_text

    return text


def clean_text(text):
    return re.sub(r"[ \t]+", " ", text).strip()


def detect_customer(text):
    upper = text.upper()

    if "COMMSCOPE" in upper:
        return "CommScope"

    if "TE CONNECTIVITY" in upper or "TE" in upper:
        return "TE Connectivity"

    return "Unknown"


def extract_po_number(text):
    patterns = [
        r"Purchase\s+Order\s+No\.?\s*[:#]?\s*(\d{6,})",
        r"PO\s+Number\s*[:#]?\s*(\d{6,})",
        r"\b(800\d{6,})\b",
        r"\b(\d{10})\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)

    return ""


def normalize_date(date_text):
    if not date_text:
        return ""

    date_text = date_text.strip()
    parts = date_text.replace("-", " ").split()

    if len(parts) == 3:
        day, month, year = parts
        month_key = month[:3].upper()
        month = MONTHS.get(month_key, month.title())
        return f"{day}-{month}-{year}"

    return date_text


def extract_dates(text):
    dates = re.findall(
        r"\b(\d{1,2}[\s\-](?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[\s\-]\d{4})\b",
        text,
        re.IGNORECASE
    )

    dates = [normalize_date(d) for d in dates]

    po_date = dates[0] if len(dates) >= 1 else ""
    delivery_date = dates[-1] if len(dates) >= 2 else po_date

    return po_date, delivery_date


def extract_product(text):
    patterns = [
        r"\b(NPC[A-Z0-9\-]+)\b",
        r"\b(NPP[A-Z0-9\-]+)\b",
        r"\b([A-Z0-9]{3,}[A-Z0-9\-]*-[A-Z0-9\-]{3,})\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ""


def extract_quantity(text, product):
    if not product:
        return 0

    lines = text.splitlines()

    for line in lines:
        if product.upper() in line.upper():
            after_product = line.upper().split(product.upper(), 1)[-1]
            numbers = re.findall(r"\b\d{1,6}\b", after_product)

            for number in numbers:
                qty = int(number)
                if qty > 0:
                    return qty

    return 0


def extract_po_from_pdf(pdf_path):
    text = read_pdf_text(pdf_path)
    text = clean_text(text)

    customer = detect_customer(text)
    po_number = extract_po_number(text)
    po_date, delivery_date = extract_dates(text)
    product = extract_product(text)
    quantity = extract_quantity(text, product)

    return {
        "customer": customer,
        "po_number": po_number,
        "po_date": po_date,
        "delivery_date": delivery_date,
        "lines": [
            {
                "item_code": product,
                "quantity": quantity
            }
        ],
        "raw_text_preview": text[:1000]
    }