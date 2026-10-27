from app.database.database import get_connection


def order_exists(po_number, product):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM orders
        WHERE po = ?
          AND product = ?
        LIMIT 1
    """, (
        po_number,
        product
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def save_verified_order(order):
    """
    Enregistre une commande après Vérification 1.
    """

    if order_exists(
        order["po_number"],
        order["product"]
    ):
        return {
            "success": False,
            "message": "Cette commande existe déjà."
        }

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO orders (
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order.get("po_date"),
        order.get("delivery_date"),
        order.get("po_number"),
        order.get("product"),
        order.get("quantity"),
        order.get("mt"),
        str(order.get("upc") or ""),
        order.get("customer"),
        "VERIFICATION_1_OK",
        1,
        0
    ))

    connection.commit()

    order_id = cursor.lastrowid

    connection.close()

    return {
        "success": True,
        "order_id": order_id,
        "message": "Commande enregistrée."
    }