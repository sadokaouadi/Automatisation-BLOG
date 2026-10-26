def normalize_customer(customer):
    if customer is None:
        return ""

    return str(customer).strip().upper()


def detect_client(customer):
    """
    Identifie le client et retourne le module métier à utiliser.
    """

    value = normalize_customer(customer)

    if "COMMSCOPE" in value:
        return {
            "found": True,
            "client_key": "COMMSCOPE",
            "display_name": "CommScope",
            "blog_type": "RJ45",
            "analyzer": "COMMSCOPE_RJ45"
        }

    # Les 2 autres clients seront ajoutés
    # lorsque nous analyserons leurs vrais BLOG.

    return {
        "found": False,
        "client_key": None,
        "display_name": customer,
        "blog_type": None,
        "analyzer": None
    }