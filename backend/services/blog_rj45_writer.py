import shutil
from pathlib import Path

import pythoncom
import win32com.client as win32


XL_UP = -4162
XL_PASTE_ALL = -4104


def normalize(value):
    if value is None:
        return ""

    if isinstance(value, float):
        if value.is_integer():
            value = int(value)

    if isinstance(value, int):
        value = str(value)

    return str(value).strip().replace(" ", "").upper()


def add_order_to_rj45_blog(
    input_blog_path,
    output_blog_path,
    order_date,
    customer_date,
    po_number,
    product,
    qty,
    mt,
    upc
):
    input_blog_path = Path(input_blog_path).resolve()
    output_blog_path = Path(output_blog_path).resolve()

    if not input_blog_path.exists():
        raise FileNotFoundError(f"Fichier BLOG introuvable : {input_blog_path}")

    output_blog_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(input_blog_path, output_blog_path)

    excel = None
    wb = None

    try:
        # Obligatoire avec Streamlit / threads Windows
        pythoncom.CoInitialize()

        excel = win32.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False

        wb = excel.Workbooks.Open(str(output_blog_path))
        ws = wb.Worksheets("RJ45")

        target_po = normalize(po_number)
        target_product = normalize(product)

        last_row = ws.Cells(ws.Rows.Count, 4).End(XL_UP).Row

        # Anti-doublon : PO + PRODUIT
        for row in range(1, last_row + 1):
            current_po = normalize(ws.Cells(row, 3).Value)
            current_product = normalize(ws.Cells(row, 4).Value)

            if current_po == target_po and current_product == target_product:
                wb.Close(SaveChanges=False)
                excel.Quit()

                return {
                    "status": "ALREADY_EXISTS",
                    "message": "Commande déjà existante dans le BLOG RJ45.",
                    "row": row,
                    "po_number": po_number,
                    "product": product,
                    "output_file": str(output_blog_path)
                }

        new_row = last_row + 1

        # Copier formules + style + couleurs
        ws.Rows(last_row).Copy()
        ws.Rows(new_row).PasteSpecial(Paste=XL_PASTE_ALL)
        excel.CutCopyMode = False

        # Remplir colonnes principales
        ws.Cells(new_row, 1).Value = order_date
        ws.Cells(new_row, 2).Value = customer_date
        ws.Cells(new_row, 3).Value = po_number
        ws.Cells(new_row, 4).Value = product
        ws.Cells(new_row, 5).Value = qty
        ws.Cells(new_row, 6).Value = mt
        ws.Cells(new_row, 7).Value = upc

        wb.Save()
        wb.Close(SaveChanges=True)
        excel.Quit()

        return {
            "status": "ADDED",
            "message": "Nouvelle commande ajoutée dans le BLOG RJ45.",
            "row": new_row,
            "po_number": po_number,
            "product": product,
            "qty": qty,
            "mt": mt,
            "upc": upc,
            "output_file": str(output_blog_path)
        }

    except Exception as e:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except:
            pass

        try:
            if excel is not None:
                excel.Quit()
        except:
            pass

        raise e

    finally:
        try:
            pythoncom.CoUninitialize()
        except:
            pass