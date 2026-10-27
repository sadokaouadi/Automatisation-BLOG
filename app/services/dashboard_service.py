from pathlib import Path

from app.database.database import get_connection

from app.services.clients.commscope.stock_service import (
    get_all_current_stock
)

from app.services.clients.commscope.rj45_stock_analyzer import (
    analyze_rj45_stock
)


# =========================================================
# CONFIGURATION
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

COMMSCOPE_BLOG = (
    PROJECT_ROOT
    / "data"
    / "imports"
    / "BLOG_2026_RJ45.xlsx"
)

# Seuil temporaire global
MIN_STOCK_WARNING = 1000


# =========================================================
# KPI COMMANDES
# =========================================================

def get_order_kpis():

    connection = get_connection()
    cursor = connection.cursor()

    # -----------------------------------------------------
    # COMMANDES HISTORIQUES
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'HISTORIQUE'
    """)

    historical_orders = cursor.fetchone()[0]
    total_orders = historical_orders

    # -----------------------------------------------------
    # COMMANDES ACTIVES
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status IS NULL
           OR status <> 'HISTORIQUE'
    """)

    active_orders = cursor.fetchone()[0]
    total_orders += active_orders

    # -----------------------------------------------------
    # VERIFICATION 1 VALIDEE
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE (
            status IS NULL
            OR status <> 'HISTORIQUE'
        )
        AND verification_1 = 1
    """)

    verification_1_ok = cursor.fetchone()[0]

    # -----------------------------------------------------
    # VERIFICATION 1 A FAIRE
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE (
            status IS NULL
            OR status <> 'HISTORIQUE'
        )
        AND verification_1 = 0
    """)

    verification_1_pending = cursor.fetchone()[0]

    # -----------------------------------------------------
    # VERIFICATION 2 A FAIRE
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE (
            status IS NULL
            OR status <> 'HISTORIQUE'
        )
        AND verification_1 = 1
        AND verification_2 = 0
        AND (
            status IS NULL
            OR status <> 'READY_ERP'
        )
    """)

    verification_2_pending = cursor.fetchone()[0]

    # -----------------------------------------------------
    # PRETES ERP
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'READY_ERP'
    """)

    ready_erp = cursor.fetchone()[0]

    # -----------------------------------------------------
    # QUANTITE ACTIVE
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COALESCE(
            SUM(quantity),
            0
        )
        FROM orders
        WHERE status IS NULL
           OR status <> 'HISTORIQUE'
    """)

    active_quantity = cursor.fetchone()[0] or 0

    # -----------------------------------------------------
    # COMMANDES RECUES AUJOURD'HUI
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE (
            status IS NULL
            OR status <> 'HISTORIQUE'
        )
        AND DATE(
            created_at,
            'localtime'
        ) = DATE(
            'now',
            'localtime'
        )
    """)

    today_orders = cursor.fetchone()[0]

    # -----------------------------------------------------
    # COMMANDES 7 DERNIERS JOURS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE (
            status IS NULL
            OR status <> 'HISTORIQUE'
        )
        AND datetime(created_at)
            >= datetime(
                'now',
                '-7 days'
            )
    """)

    last_7_days = cursor.fetchone()[0]

    connection.close()

    return {
        "total_orders": total_orders,
        "historical_orders": historical_orders,
        "active_orders": active_orders,
        "verification_1_ok": verification_1_ok,
        "verification_1_pending": verification_1_pending,
        "verification_2_pending": verification_2_pending,
        "ready_erp": ready_erp,
        "active_quantity": active_quantity,
        "today_orders": today_orders,
        "last_7_days": last_7_days
    }


# =========================================================
# RESUME STOCK GLOBAL
# =========================================================

def get_stock_summary():

    stock_items = get_all_current_stock()

    available = 0
    low = 0
    rupture = 0
    unknown = 0

    for item in stock_items:

        stock = item.get("stock")

        if stock is None:

            unknown += 1

        elif stock <= 0:

            rupture += 1

        elif stock < MIN_STOCK_WARNING:

            low += 1

        else:

            available += 1

    alerts = (
        low
        + rupture
        + unknown
    )

    return {
        "total": len(stock_items),
        "available": available,
        "low": low,
        "rupture": rupture,
        "unknown": unknown,
        "alerts": alerts
    }


# =========================================================
# ANALYSER STOCK D'UNE COMMANDE
# =========================================================

def evaluate_order_stock(
    customer,
    product,
    quantity
):

    customer_text = str(
        customer or ""
    ).upper()

    # -----------------------------------------------------
    # AUTRE CLIENT PAS ENCORE CONFIGURE
    # -----------------------------------------------------

    if (
        customer_text
        and "COMMSCOPE" not in customer_text
    ):

        return {
            "level": "UNKNOWN",
            "label": "⚠ Non configuré",
            "is_risk": True
        }

    # -----------------------------------------------------
    # DONNEES MANQUANTES
    # -----------------------------------------------------

    if (
        not product
        or quantity is None
    ):

        return {
            "level": "UNKNOWN",
            "label": "⚠ À vérifier",
            "is_risk": True
        }

    # -----------------------------------------------------
    # ANALYSE COMMSCOPE
    # -----------------------------------------------------

    try:

        result = analyze_rj45_stock(
            blog_path=COMMSCOPE_BLOG,
            product_code=str(product),
            requested_qty=float(quantity)
        )

    except Exception:

        return {
            "level": "UNKNOWN",
            "label": "⚠ Analyse impossible",
            "is_risk": True
        }

    # -----------------------------------------------------
    # PRODUIT NON TROUVE
    # -----------------------------------------------------

    if not result.get(
        "found",
        False
    ):

        return {
            "level": "UNKNOWN",
            "label": "⚠ Produit inconnu",
            "is_risk": True
        }

    global_status = result.get(
        "status"
    )

    components = result.get(
        "components",
        []
    )

    # -----------------------------------------------------
    # RUPTURE APRES COMMANDE
    # -----------------------------------------------------

    if global_status == "INSUFFICIENT":

        return {
            "level": "CRITICAL",
            "label": "🔴 Stock insuffisant",
            "is_risk": True
        }

    # -----------------------------------------------------
    # STOCK INCONNU
    # -----------------------------------------------------

    if global_status == "UNKNOWN":

        return {
            "level": "UNKNOWN",
            "label": "⚠ Stock à vérifier",
            "is_risk": True
        }

    # -----------------------------------------------------
    # STOCK PROJETE FAIBLE
    # -----------------------------------------------------

    for component in components:

        projected_stock = component.get(
            "projected_stock"
        )

        if projected_stock is None:
            continue

        if (
            0 <= projected_stock
            < MIN_STOCK_WARNING
        ):

            return {
                "level": "WARNING",
                "label": "🟠 Stock faible",
                "is_risk": True
            }

    # -----------------------------------------------------
    # STOCK OK
    # -----------------------------------------------------

    return {
        "level": "OK",
        "label": "🟢 Stock OK",
        "is_risk": False
    }


# =========================================================
# COMMANDES A RISQUE
# =========================================================

def get_risk_orders():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            po,
            customer,
            product,
            quantity

        FROM orders

        WHERE (
            status IS NULL
            OR status <> 'HISTORIQUE'
        )

        AND verification_1 = 1
        AND verification_2 = 0
    """)

    rows = cursor.fetchall()

    connection.close()

    risk_orders = []

    for row in rows:

        stock_result = evaluate_order_stock(
            customer=row[2],
            product=row[3],
            quantity=row[4]
        )

        if stock_result["is_risk"]:

            risk_orders.append({
                "id": row[0],
                "po": row[1],
                "customer": row[2],
                "product": row[3],
                "quantity": row[4],
                "stock_status": stock_result["label"]
            })

    return risk_orders


# =========================================================
# DERNIERES COMMANDES
# =========================================================

def get_recent_orders(
    limit=10
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            date,
            po,
            customer,
            product,
            quantity,
            status,
            verification_1,
            verification_2

        FROM orders

        ORDER BY id DESC

        LIMIT ?
    """, (
        limit,
    ))

    rows = cursor.fetchall()

    connection.close()

    results = []

    for row in rows:

        status = row[6]

        order = {
            "id": row[0],
            "date": row[1],
            "po": row[2],
            "customer": row[3],
            "product": row[4],
            "quantity": row[5],
            "status": status,
            "verification_1": row[7],
            "verification_2": row[8],
            "stock_status": "-"
        }

        # Ne pas analyser les anciennes commandes historiques
        if status != "HISTORIQUE":

            stock_result = evaluate_order_stock(
                customer=row[3],
                product=row[4],
                quantity=row[5]
            )

            order["stock_status"] = (
                stock_result["label"]
            )

        results.append(
            order
        )

    return results


# =========================================================
# DASHBOARD COMPLET
# =========================================================

def get_dashboard_data():

    orders = get_order_kpis()

    stock = get_stock_summary()

    risk_orders = get_risk_orders()

    recent_orders = get_recent_orders(
        limit=10
    )

    return {
        "orders": orders,
        "stock": stock,
        "risk_orders": risk_orders,
        "risk_orders_count": len(
            risk_orders
        ),
        "recent_orders": recent_orders
    }