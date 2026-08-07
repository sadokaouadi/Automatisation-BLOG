from pathlib import Path


# =====================================================
# CHEMINS DU PROJET
# =====================================================

# backend/services/client_blog_router.py
# parent        = services
# parent.parent = backend
BACKEND_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BACKEND_DIR / "data" / "input"
OUTPUT_DIR = BACKEND_DIR / "data" / "output"

ORIGINAL_RJ45_BLOG = INPUT_DIR / "BLOG 2026 - Rj45_cleaned.xlsx"
TE_BLOG = INPUT_DIR / "BLOG 2025 - TE.xlsx"


BLOG_CONFIG = {
    "COMMSCOPE": {
        "main_sheet": "RJ45",
        "client_type": "RJ45"
    },
    "TE CONNECTIVITY": {
        "main_sheet": None,
        "client_type": "TE"
    }
}


def normalize_text(value):
    if value is None:
        return ""

    return str(value).strip().upper()


def detect_client_key(customer_name):
    customer = normalize_text(customer_name)

    if "COMMSCOPE" in customer:
        return "COMMSCOPE"

    if "TE CONNECTIVITY" in customer or customer == "TE":
        return "TE CONNECTIVITY"

    return None


def get_latest_rj45_blog():
    """
    Retourne le dernier BLOG RJ45 généré.

    S'il n'existe encore aucun BLOG généré,
    retourne le BLOG RJ45 original.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated_blogs = [
        file
        for file in OUTPUT_DIR.glob("BLOG_RJ45_generated_*.xlsx")
        if file.is_file()
    ]

    if generated_blogs:
        # Prendre le fichier généré le plus récent
        latest_blog = max(
            generated_blogs,
            key=lambda file: file.stat().st_mtime
        )

        return latest_blog, "LATEST_GENERATED"

    return ORIGINAL_RJ45_BLOG, "ORIGINAL"


def get_blog_config(customer_name):
    client_key = detect_client_key(customer_name)

    if client_key is None:
        return {
            "found": False,
            "customer": customer_name,
            "message": "Client inconnu, aucun BLOG associé."
        }

    config = BLOG_CONFIG[client_key]

    if client_key == "COMMSCOPE":
        blog_path, blog_source = get_latest_rj45_blog()

    elif client_key == "TE CONNECTIVITY":
        blog_path = TE_BLOG
        blog_source = "ORIGINAL"

    else:
        return {
            "found": False,
            "customer": customer_name,
            "message": "Configuration BLOG introuvable."
        }

    return {
        "found": True,
        "customer": customer_name,
        "client_key": client_key,
        "blog_path": str(blog_path),
        "blog_source": blog_source,
        "main_sheet": config["main_sheet"],
        "client_type": config["client_type"],
        "file_exists": blog_path.exists()
    }