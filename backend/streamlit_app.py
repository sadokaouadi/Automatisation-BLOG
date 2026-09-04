import shutil
from datetime import datetime
from pathlib import Path

import streamlit as st

from services.pdf_po_extractor import extract_po_from_pdf
from services.client_blog_router import get_blog_config
from services.blog_product_lookup import find_product_in_rj45_blog
from services.blog_rj45_writer import add_order_to_rj45_blog
from services.rj45_stock_analyzer import analyze_rj45_stock


# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Order Automation System",
    page_icon="📦",
    layout="wide"
)

UPLOAD_DIR = Path("data/uploads")
OUTPUT_DIR = Path("data/output")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# FONCTIONS UTILITAIRES
# =========================================================

def safe_float(value):
    """
    Convertit une valeur en float.
    """

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value):
    """
    Affichage propre des valeurs numériques.
    """

    if value is None:
        return "-"

    try:
        value = float(value)

        if value.is_integer():
            return f"{value:,.0f}"

        return f"{value:,.2f}"

    except (TypeError, ValueError):
        return str(value)


def clear_order_form_state():
    """
    Supprime les anciennes valeurs des champs Streamlit
    avant une nouvelle extraction PDF.

    Streamlit conserve les valeurs des widgets ayant la même clé.
    Sans ce nettoyage, un nouveau PDF peut garder les anciennes
    valeurs vides au lieu d'afficher les nouvelles données extraites.
    """

    prefixes = (
        "customer_",
        "po_",
        "order_date_",
        "customer_date_",
        "product_",
        "qty_",
        "mt_",
        "upc_"
    )

    keys_to_delete = [
        key
        for key in list(st.session_state.keys())
        if key.startswith(prefixes)
    ]

    for key in keys_to_delete:
        del st.session_state[key]


# =========================================================
# AFFICHAGE DE L'ALERTE STOCK RJ45
# =========================================================

def show_rj45_stock_alert(
    stock_result,
    alert_key
):
    """
    Affiche l'état du stock AVANT génération du BLOG.

    Le calcul est basé sur :
    - les composants utilisés historiquement par le produit ;
    - la consommation par produit ;
    - le stock actuel de chaque composant ;
    - la quantité de la nouvelle commande.
    """

    # -----------------------------------------------------
    # Produit ou stock impossible à analyser
    # -----------------------------------------------------

    if not stock_result.get("found"):

        message = stock_result.get(
            "message",
            "Impossible d'analyser le stock."
        )

        st.warning(
            f"⚠️ Analyse stock impossible : {message}"
        )

        return

    status = stock_result.get("status")

    product = stock_result.get(
        "product",
        ""
    )

    requested_qty = stock_result.get(
        "requested_qty",
        0
    )

    components_count = stock_result.get(
        "components_count",
        0
    )

    insufficient_count = stock_result.get(
        "insufficient_count",
        0
    )

    limiting = stock_result.get(
        "limiting_component"
    )

    # -----------------------------------------------------
    # STOCK SUFFISANT
    # -----------------------------------------------------

    if status == "SUFFICIENT":

        st.success(
            f"✅ STOCK SUFFISANT — {product}\n\n"
            f"Quantité demandée : "
            f"{format_number(requested_qty)}\n\n"
            f"{components_count} composant(s) vérifié(s)."
        )

        toast_message = (
            f"Stock suffisant pour {product}"
        )

        toast_icon = "✅"

    # -----------------------------------------------------
    # STOCK INSUFFISANT
    # -----------------------------------------------------

    elif status == "INSUFFICIENT":

        message = (
            f"🔴 STOCK INSUFFISANT — {product}\n\n"
            f"Quantité demandée : "
            f"{format_number(requested_qty)}\n\n"
            f"{insufficient_count} composant(s) "
            f"insuffisant(s) sur "
            f"{components_count}."
        )

        if limiting:

            message += (
                "\n\n"
                "Composant le plus critique : "
                f"{limiting.get('component', '')}"
                "\n\n"
                "Stock actuel : "
                f"{format_number(limiting.get('current_stock'))}"
                "\n\n"
                "Besoin : "
                f"{format_number(limiting.get('required_qty'))}"
                "\n\n"
                "Stock après commande : "
                f"{format_number(limiting.get('projected_stock'))}"
            )

        st.error(message)

        toast_message = (
            f"Stock insuffisant pour {product}"
        )

        toast_icon = "🔴"

    # -----------------------------------------------------
    # STOCK INCONNU
    # -----------------------------------------------------

    else:

        st.warning(
            f"⚠️ STOCK NON DÉTERMINÉ — {product}\n\n"
            "Certaines informations de stock "
            "ne sont pas disponibles."
        )

        toast_message = (
            f"Stock non déterminé pour {product}"
        )

        toast_icon = "⚠️"

    # -----------------------------------------------------
    # Petit popup Streamlit
    # -----------------------------------------------------

    shown_alerts = st.session_state.setdefault(
        "shown_stock_alerts",
        []
    )

    if alert_key not in shown_alerts:

        st.toast(
            toast_message,
            icon=toast_icon
        )

        shown_alerts.append(
            alert_key
        )

    # -----------------------------------------------------
    # Détails facultatifs
    # -----------------------------------------------------

    components = stock_result.get(
        "components",
        []
    )

    if components:

        with st.expander(
            "📊 Voir le détail des composants"
        ):

            component_rows = []

            for component in components:

                component_rows.append({
                    "Composant":
                        component.get("component"),

                    "Conso / produit":
                        component.get(
                            "consumption_per_unit"
                        ),

                    "Stock actuel":
                        component.get(
                            "current_stock"
                        ),

                    "Besoin commande":
                        component.get(
                            "required_qty"
                        ),

                    "Stock projeté":
                        component.get(
                            "projected_stock"
                        ),

                    "État":
                        component.get(
                            "status"
                        )
                })

            st.dataframe(
                component_rows,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# GÉNÉRATION DE PLUSIEURS COMMANDES DANS UN SEUL BLOG
# =========================================================

def generate_batch_blog(
    orders,
    input_blog_path,
    final_output_path
):
    """
    Génère un seul BLOG contenant toutes
    les nouvelles commandes.

    Exemple :

    BLOG actuel
        ↓
    + commande PDF 1
        ↓
    + commande PDF 2
        ↓
    + commande PDF 3
        ↓
    BLOG final
    """

    if not orders:
        raise ValueError(
            "Aucune commande prête pour la génération."
        )

    current_blog = Path(
        input_blog_path
    ).resolve()

    final_output_path = Path(
        final_output_path
    ).resolve()

    temporary_files = []
    results = []

    batch_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    try:

        # -------------------------------------------------
        # Ajouter les commandes une par une
        # -------------------------------------------------

        for index, order in enumerate(
            orders,
            start=1
        ):

            temporary_output = (
                OUTPUT_DIR /
                f"_temp_batch_{batch_id}_{index}.xlsx"
            ).resolve()

            result = add_order_to_rj45_blog(

                input_blog_path=str(
                    current_blog
                ),

                output_blog_path=str(
                    temporary_output
                ),

                order_date=order[
                    "order_date"
                ],

                customer_date=order[
                    "customer_date"
                ],

                po_number=order[
                    "po_number"
                ],

                product=order[
                    "product"
                ],

                qty=order[
                    "qty"
                ],

                mt=order[
                    "mt"
                ],

                upc=order[
                    "upc"
                ]
            )

            result["source_pdf"] = order[
                "source_pdf"
            ]

            results.append(
                result
            )

            generated_step = Path(
                result["output_file"]
            ).resolve()

            if not generated_step.exists():

                raise FileNotFoundError(
                    "Le fichier intermédiaire "
                    "n'a pas été créé : "
                    f"{generated_step}"
                )

            temporary_files.append(
                generated_step
            )

            # Le fichier créé devient la base
            # pour la commande suivante.
            current_blog = generated_step

        # -------------------------------------------------
        # Créer le BLOG final
        # -------------------------------------------------

        final_output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copyfile(
            current_blog,
            final_output_path
        )

        return {

            "status": "DONE",

            "output_file":
                str(final_output_path),

            "total":
                len(results),

            "added":
                sum(
                    1
                    for result in results
                    if result.get("status")
                    == "ADDED"
                ),

            "duplicates":
                sum(
                    1
                    for result in results
                    if result.get("status")
                    == "ALREADY_EXISTS"
                ),

            "results":
                results
        }

    finally:

        # -------------------------------------------------
        # Supprimer les fichiers temporaires
        # -------------------------------------------------

        for temp_file in temporary_files:

            try:

                if temp_file.exists():
                    temp_file.unlink()

            except OSError:
                pass


# =========================================================
# INTERFACE
# =========================================================

st.title(
    "📦 Order Automation System"
)

st.subheader(
    "Plusieurs PDF clients → un seul BLOG Excel modifié"
)

st.info(
    "Importez plusieurs Purchase Orders PDF, "
    "vérifiez les données extraites, contrôlez "
    "automatiquement le stock des composants "
    "puis générez un seul BLOG RJ45."
)


# =========================================================
# 1. IMPORT DES PDF
# =========================================================

st.markdown(
    "## 1. Importer les PDF clients"
)

uploaded_pdfs = st.file_uploader(

    "Choisir un ou plusieurs Purchase Orders PDF",

    type=[
        "pdf"
    ],

    accept_multiple_files=True
)


if uploaded_pdfs:

    st.write(
        f"**{len(uploaded_pdfs)} "
        f"PDF sélectionné(s).**"
    )

    if st.button(
        "🔍 Extraire tous les PDF",
        type="primary"
    ):

        # IMPORTANT :
        # Réinitialiser les anciens champs avant d'afficher
        # les données du nouveau lot de PDF.
        clear_order_form_state()

        extracted_documents = []

        progress_bar = st.progress(
            0
        )

        status_box = st.empty()

        # -------------------------------------------------
        # Extraction de tous les PDF
        # -------------------------------------------------

        for index, uploaded_pdf in enumerate(
            uploaded_pdfs,
            start=1
        ):

            status_box.write(
                f"Extraction "
                f"{index}/"
                f"{len(uploaded_pdfs)} : "
                f"`{uploaded_pdf.name}`"
            )

            pdf_path = (
                UPLOAD_DIR /
                uploaded_pdf.name
            )

            try:

                # Sauvegarde temporaire du PDF
                with open(
                    pdf_path,
                    "wb"
                ) as file:

                    file.write(
                        uploaded_pdf.getbuffer()
                    )

                # Extraction
                extracted_po = (
                    extract_po_from_pdf(
                        pdf_path
                    )
                )

                extracted_documents.append({

                    "file_name":
                        uploaded_pdf.name,

                    "status":
                        "OK",

                    "error":
                        "",

                    "data":
                        extracted_po
                })

            except Exception as exc:

                extracted_documents.append({

                    "file_name":
                        uploaded_pdf.name,

                    "status":
                        "ERROR",

                    "error":
                        str(exc),

                    "data":
                        {}
                })

            progress_bar.progress(
                index /
                len(uploaded_pdfs)
            )

        # -------------------------------------------------
        # Sauvegarde en session
        # -------------------------------------------------

        st.session_state[
            "extracted_documents"
        ] = extracted_documents

        st.session_state.pop(
            "batch_result",
            None
        )

        st.session_state[
            "shown_stock_alerts"
        ] = []

        status_box.empty()

        st.success(
            f"✅ Extraction terminée : "
            f"{len(extracted_documents)} "
            f"PDF traité(s)."
        )


# =========================================================
# ARRÊT SI AUCUN PDF EXTRAIT
# =========================================================

if "extracted_documents" not in st.session_state:

    st.warning(
        "Importez les PDF puis cliquez sur "
        "« Extraire tous les PDF »."
    )

    st.stop()


# =========================================================
# 2. VÉRIFICATION DES COMMANDES
# =========================================================

st.markdown(
    "## 2. Vérification des données extraites"
)

documents = st.session_state[
    "extracted_documents"
]

orders_to_generate = []

summary_rows = []


customer_options = [

    "CommScope",

    "TE Connectivity",

    "Amphenol Socapex"
]


# =========================================================
# PARCOURIR CHAQUE PDF
# =========================================================

for document_index, document in enumerate(
    documents
):

    file_name = document[
        "file_name"
    ]

    with st.expander(
        f"📄 {file_name}",
        expanded=document_index == 0
    ):

        # -------------------------------------------------
        # Erreur extraction
        # -------------------------------------------------

        if document["status"] == "ERROR":

            st.error(
                "Erreur d'extraction : "
                f"{document['error']}"
            )

            summary_rows.append({

                "PDF":
                    file_name,

                "PO":
                    "",

                "Produit":
                    "",

                "Quantité":
                    "",

                "Stock":
                    "Non analysé",

                "État":
                    "Erreur extraction"
            })

            continue

        # -------------------------------------------------
        # Données extraites
        # -------------------------------------------------

        extracted_po = document[
            "data"
        ]

        lines = (
            extracted_po.get("lines")
            or []
        )

        detected_customer = (
            extracted_po.get(
                "customer",
                "CommScope"
            )
        )

        if detected_customer not in customer_options:

            detected_customer = (
                "CommScope"
            )

        # -------------------------------------------------
        # Client
        # -------------------------------------------------

        customer = st.selectbox(

            "Client",

            customer_options,

            index=customer_options.index(
                detected_customer
            ),

            key=f"customer_{document_index}"
        )

        # -------------------------------------------------
        # Infos commande
        # -------------------------------------------------

        col1, col2, col3 = st.columns(
            3
        )

        with col1:

            po_number = st.text_input(

                "PO Number",

                value=str(
                    extracted_po.get(
                        "po_number",
                        ""
                    )
                ),

                key=f"po_{document_index}"
            )

        with col2:

            order_date = st.text_input(

                "Date commande",

                value=str(
                    extracted_po.get(
                        "po_date",
                        ""
                    )
                ),

                key=(
                    f"order_date_"
                    f"{document_index}"
                )
            )

        with col3:

            customer_date = st.text_input(

                "Date client / livraison",

                value=str(
                    extracted_po.get(
                        "delivery_date",
                        ""
                    )
                ),

                key=(
                    f"customer_date_"
                    f"{document_index}"
                )
            )

        # -------------------------------------------------
        # Aucun produit
        # -------------------------------------------------

        if not lines:

            st.error(
                "Aucune ligne produit détectée "
                "dans ce PDF."
            )

            summary_rows.append({

                "PDF":
                    file_name,

                "PO":
                    po_number,

                "Produit":
                    "",

                "Quantité":
                    "",

                "Stock":
                    "Non analysé",

                "État":
                    "Aucune ligne détectée"
            })

            continue

        # -------------------------------------------------
        # Pour le moment génération uniquement CommScope
        # -------------------------------------------------

        if customer != "CommScope":

            st.warning(
                "La génération automatique du BLOG "
                "est actuellement disponible uniquement "
                "pour CommScope / RJ45."
            )

        # -------------------------------------------------
        # BLOG associé
        # -------------------------------------------------

        blog_config = get_blog_config(
            customer
        )

        if not blog_config.get(
            "found"
        ):

            st.error(
                "Aucun BLOG associé à ce client."
            )

            continue

        if not blog_config.get(
            "file_exists"
        ):

            st.error(
                "Fichier BLOG introuvable : "
                f"{blog_config.get('blog_path')}"
            )

            continue

        st.caption(
            "BLOG utilisé pour l'analyse : "
            f"{blog_config.get('blog_path')}"
        )

        # =================================================
        # PARCOURIR LES ARTICLES DU PDF
        # =================================================

        for line_index, line in enumerate(
            lines
        ):

            st.markdown(
                f"### Article {line_index + 1}"
            )

            left, right = st.columns(
                2
            )

            # ---------------------------------------------
            # Produit
            # ---------------------------------------------

            with left:

                product = st.text_input(

                    "Produit / Référence",

                    value=str(
                        line.get(
                            "item_code",
                            ""
                        )
                    ),

                    key=(
                        f"product_"
                        f"{document_index}_"
                        f"{line_index}"
                    )
                )

            # ---------------------------------------------
            # Quantité
            # ---------------------------------------------

            with right:

                default_qty = int(
                    safe_float(
                        line.get(
                            "quantity"
                        )
                    )
                    or 1
                )

                qty = st.number_input(

                    "Quantité",

                    min_value=1,

                    value=default_qty,

                    step=1,

                    key=(
                        f"qty_"
                        f"{document_index}_"
                        f"{line_index}"
                    )
                )

            # =================================================
            # ALERTE STOCK AVANT GÉNÉRATION
            # =================================================

            stock_status_label = (
                "Non analysé"
            )

            if (
                customer == "CommScope"
                and product
            ):

                st.markdown(
                    "#### 📦 Vérification du stock"
                )

                try:

                    stock_result = (
                        analyze_rj45_stock(

                            blog_path=(
                                blog_config[
                                    "blog_path"
                                ]
                            ),

                            product_code=product,

                            requested_qty=qty
                        )
                    )

                    stock_status = (
                        stock_result.get(
                            "status",
                            "UNKNOWN"
                        )
                    )

                    if stock_status == "SUFFICIENT":

                        stock_status_label = (
                            "✅ Suffisant"
                        )

                    elif stock_status == "INSUFFICIENT":

                        stock_status_label = (
                            "🔴 Insuffisant"
                        )

                    else:

                        stock_status_label = (
                            "⚠️ Non déterminé"
                        )

                    alert_key = (

                        f"{file_name}|"
                        f"{po_number}|"
                        f"{product}|"
                        f"{qty}|"
                        f"{stock_status}"
                    )

                    show_rj45_stock_alert(
                        stock_result,
                        alert_key
                    )

                except Exception as exc:

                    stock_status_label = (
                        "⚠️ Erreur analyse"
                    )

                    st.warning(
                        "⚠️ Analyse du stock "
                        "impossible : "
                        f"{exc}"
                    )

            # =================================================
            # RECHERCHE mt + UPC
            # =================================================

            st.markdown(
                "#### 🔎 Informations produit"
            )

            ready = False

            mt = None

            upc = None

            state_label = (
                "Non prêt"
            )

            # -------------------------------------------------
            # CommScope
            # -------------------------------------------------

            if (
                customer == "CommScope"
                and product
            ):

                product_info = (
                    find_product_in_rj45_blog(

                        blog_config[
                            "blog_path"
                        ],

                        product
                    )
                )

                # ---------------------------------------------
                # Produit trouvé
                # ---------------------------------------------

                if product_info.get(
                    "found"
                ):

                    mt = product_info.get(
                        "mt"
                    )

                    upc = product_info.get(
                        "upc"
                    )

                    metric1, metric2, metric3 = (
                        st.columns(3)
                    )

                    with metric1:

                        st.metric(
                            "mt",
                            mt
                        )

                    with metric2:

                        st.metric(
                            "UPC",
                            upc
                        )

                    with metric3:

                        st.metric(
                            "Ligne historique",
                            product_info.get(
                                "row"
                            )
                        )

                    ready = bool(

                        mt not in [
                            None,
                            ""
                        ]

                        and

                        upc not in [
                            None,
                            ""
                        ]
                    )

                    if ready:

                        state_label = (
                            "Prêt"
                        )

                    else:

                        state_label = (
                            "mt/UPC manquant"
                        )

                # ---------------------------------------------
                # Produit non trouvé
                # ---------------------------------------------

                else:

                    st.warning(
                        "Produit introuvable "
                        "dans l'historique RJ45."
                    )

                    st.info(
                        "Saisissez mt et UPC "
                        "après validation du manager."
                    )

                    manual1, manual2 = (
                        st.columns(2)
                    )

                    with manual1:

                        mt = st.text_input(

                            "mt manuel",

                            key=(
                                f"mt_"
                                f"{document_index}_"
                                f"{line_index}"
                            )
                        )

                    with manual2:

                        upc = st.text_input(

                            "UPC manuel",

                            key=(
                                f"upc_"
                                f"{document_index}_"
                                f"{line_index}"
                            )
                        )

                    ready = bool(
                        mt and upc
                    )

                    if ready:

                        state_label = (
                            "Prêt avec saisie manuelle"
                        )

                    else:

                        state_label = (
                            "Validation requise"
                        )

            # -------------------------------------------------
            # Autres clients
            # -------------------------------------------------

            else:

                state_label = (
                    "Client non encore pris en charge"
                )

            # =================================================
            # COMMANDE PRÊTE
            # =================================================

            if (
                ready
                and customer == "CommScope"
            ):

                orders_to_generate.append({

                    "source_pdf":
                        file_name,

                    "customer":
                        customer,

                    "po_number":
                        po_number,

                    "order_date":
                        order_date,

                    "customer_date":
                        customer_date,

                    "product":
                        product,

                    "qty":
                        qty,

                    "mt":
                        mt,

                    "upc":
                        upc
                })

            # =================================================
            # RÉSUMÉ
            # =================================================

            summary_rows.append({

                "PDF":
                    file_name,

                "PO":
                    po_number,

                "Produit":
                    product,

                "Quantité":
                    qty,

                "Stock":
                    stock_status_label,

                "État":
                    state_label
            })

        # -------------------------------------------------
        # Texte brut PDF
        # -------------------------------------------------

        with st.expander(
            "Voir l'extrait du texte PDF"
        ):

            st.text(
                extracted_po.get(
                    "raw_text_preview",
                    ""
                )
            )


# =========================================================
# 3. RÉSUMÉ DU LOT
# =========================================================

st.markdown(
    "## 3. Résumé du lot"
)

st.dataframe(
    summary_rows,
    use_container_width=True,
    hide_index=True
)

ready_count = len(
    orders_to_generate
)

total_lines = len(
    summary_rows
)

metric1, metric2, metric3 = (
    st.columns(3)
)

with metric1:

    st.metric(
        "PDF traités",
        len(documents)
    )

with metric2:

    st.metric(
        "Lignes détectées",
        total_lines
    )

with metric3:

    st.metric(
        "Commandes prêtes",
        ready_count
    )


# =========================================================
# 4. GÉNÉRATION D'UN SEUL BLOG
# =========================================================

st.markdown(
    "## 4. Générer un seul BLOG RJ45"
)

if ready_count == 0:

    st.warning(
        "Aucune commande CommScope "
        "n'est prête pour la génération."
    )

else:

    st.success(
        f"{ready_count} commande(s) "
        "seront ajoutée(s) "
        "dans un seul BLOG."
    )


if st.button(

    "✅ Générer le BLOG avec toutes les commandes",

    disabled=(
        ready_count == 0
    ),

    type="primary"
):

    # -----------------------------------------------------
    # Récupérer le dernier BLOG disponible
    # -----------------------------------------------------

    blog_config = get_blog_config(
        "CommScope"
    )

    if not blog_config.get(
        "found"
    ):

        st.error(
            "Configuration CommScope introuvable."
        )

        st.stop()

    if not blog_config.get(
        "file_exists"
    ):

        st.error(
            "BLOG source introuvable : "
            f"{blog_config.get('blog_path')}"
        )

        st.stop()

    # -----------------------------------------------------
    # Nom du BLOG final
    #
    # IMPORTANT :
    # on garde BLOG_RJ45_generated_
    # pour que client_blog_router.py puisse
    # retrouver automatiquement le dernier BLOG.
    # -----------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_blog = (

        OUTPUT_DIR /

        f"BLOG_RJ45_generated_"
        f"{timestamp}.xlsx"
    )

    try:

        with st.spinner(
            "Ajout de toutes les commandes "
            "dans le BLOG..."
        ):

            batch_result = generate_batch_blog(

                orders=(
                    orders_to_generate
                ),

                input_blog_path=(
                    blog_config[
                        "blog_path"
                    ]
                ),

                final_output_path=(
                    output_blog
                )
            )

        st.session_state[
            "batch_result"
        ] = batch_result

    except Exception as exc:

        st.error(
            "Erreur pendant la génération "
            f"du BLOG : {exc}"
        )


# =========================================================
# 5. RÉSULTAT
# =========================================================

batch_result = st.session_state.get(
    "batch_result"
)

if batch_result:

    st.markdown(
        "## 5. Résultat"
    )

    st.success(
        f"✅ BLOG généré : "
        f"{batch_result['added']} ajout(s), "
        f"{batch_result['duplicates']} doublon(s)."
    )

    result_rows = []

    for result in batch_result[
        "results"
    ]:

        result_rows.append({

            "PDF":
                result.get(
                    "source_pdf",
                    ""
                ),

            "PO":
                result.get(
                    "po_number",
                    ""
                ),

            "Produit":
                result.get(
                    "product",
                    ""
                ),

            "Statut":
                result.get(
                    "status",
                    ""
                ),

            "Ligne":
                result.get(
                    "row",
                    ""
                )
        })

    st.dataframe(
        result_rows,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------------------------------
    # Téléchargement
    # -----------------------------------------------------

    output_path = Path(
        batch_result[
            "output_file"
        ]
    )

    if output_path.exists():

        with open(
            output_path,
            "rb"
        ) as file:

            st.download_button(

                label=(
                    "⬇️ Télécharger "
                    "le BLOG final"
                ),

                data=file,

                file_name=(
                    output_path.name
                ),

                mime=(
                    "application/"
                    "vnd.openxmlformats-"
                    "officedocument."
                    "spreadsheetml.sheet"
                )
            )