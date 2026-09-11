"""Builds the Ridgeline_Orders.xlsx workbook from the live database.

Used by the /export/ridgeline.xlsx route. Every derived number is a real
Excel formula (SUMIFS/COUNTIFS/IF), not a value computed in Python and
pasted in, so the sheet stays live if someone edits it in Excel.
"""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from app.models import (
    Order, Customer, Product, GreenCoffeeLot, RoastBatch, Subscription,
)

HEADER_FILL = PatternFill(start_color="3B2A20", end_color="3B2A20", fill_type="solid")
HEADER_FONT = Font(name="Arial", bold=True, color="F6F0E4")
BODY_FONT = Font(name="Arial", size=10)
CURRENCY_FMT = "$#,##0.00"
PCT_FMT = "0.0%"
MAX_ROW = 500  # generous fixed range for SUMIFS/COUNTIFS so formulas don't need resizing


def _write_header(ws, headers):
    for col, label in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=label)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 20


def _autosize(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def _style_body(ws, first_row, last_row, ncols):
    for r in range(first_row, last_row + 1):
        for c in range(1, ncols + 1):
            ws.cell(row=r, column=c).font = BODY_FONT


def build_workbook():
    orders = Order.query.order_by(Order.order_date).all()
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.order_by(Product.sku).all()
    lots = GreenCoffeeLot.query.order_by(GreenCoffeeLot.lot_code).all()
    batches = RoastBatch.query.order_by(RoastBatch.roast_date).all()
    subs = Subscription.query.order_by(Subscription.customer_id).all()

    wb = Workbook()

    # ---------------- Order Items (written first so Orders can reference it) ----------------
    ws_items = wb.active
    ws_items.title = "Order Items"
    _write_header(ws_items, ["Order Number", "Product SKU", "Product Name", "Quantity", "Unit Price", "Line Total"])
    row = 2
    for o in orders:
        for item in o.items:
            ws_items.cell(row=row, column=1, value=o.order_number)
            ws_items.cell(row=row, column=2, value=item.product.sku)
            ws_items.cell(row=row, column=3, value=item.product.name)
            ws_items.cell(row=row, column=4, value=item.quantity)
            c5 = ws_items.cell(row=row, column=5, value=float(item.unit_price))
            c5.number_format = CURRENCY_FMT
            c6 = ws_items.cell(row=row, column=6, value=f"=D{row}*E{row}")
            c6.number_format = CURRENCY_FMT
            row += 1
    _style_body(ws_items, 2, max(row - 1, 2), 6)
    _autosize(ws_items, [16, 14, 24, 10, 12, 12])

    # ---------------- Orders ----------------
    ws_orders = wb.create_sheet("Orders")
    _write_header(ws_orders, [
        "Order Number", "Account", "Type", "Status", "Order Date",
        "Requested Ship", "Item Count", "Total", "Notes",
    ])
    for i, o in enumerate(orders, start=2):
        ws_orders.cell(row=i, column=1, value=o.order_number)
        ws_orders.cell(row=i, column=2, value=o.customer.name)
        ws_orders.cell(row=i, column=3, value=o.order_type)
        ws_orders.cell(row=i, column=4, value=o.status)
        d5 = ws_orders.cell(row=i, column=5, value=o.order_date.strftime("%Y-%m-%d"))
        d6 = ws_orders.cell(row=i, column=6, value=o.requested_ship_date.strftime("%Y-%m-%d") if o.requested_ship_date else None)
        c7 = ws_orders.cell(row=i, column=7,
                             value=f"=COUNTIFS('Order Items'!$A$2:$A${MAX_ROW},A{i})")
        c8 = ws_orders.cell(row=i, column=8,
                             value=f"=SUMIFS('Order Items'!$F$2:$F${MAX_ROW},'Order Items'!$A$2:$A${MAX_ROW},A{i})")
        c8.number_format = CURRENCY_FMT
        ws_orders.cell(row=i, column=9, value=o.notes or "")
    last = max(len(orders) + 1, 2)
    _style_body(ws_orders, 2, last, 9)
    _autosize(ws_orders, [18, 22, 11, 12, 13, 15, 11, 12, 34])

    # ---------------- Accounts ----------------
    ws_acc = wb.create_sheet("Accounts")
    _write_header(ws_acc, [
        "Name", "Type", "City", "State", "Country", "Currency",
        "Open Orders", "Lifetime Value", "Since",
    ])
    for i, c in enumerate(customers, start=2):
        ws_acc.cell(row=i, column=1, value=c.name)
        ws_acc.cell(row=i, column=2, value=c.type)
        ws_acc.cell(row=i, column=3, value=c.city)
        ws_acc.cell(row=i, column=4, value=c.state)
        ws_acc.cell(row=i, column=5, value=c.country)
        ws_acc.cell(row=i, column=6, value=c.currency)
        col7 = ws_acc.cell(row=i, column=7, value=(
            f"=COUNTIFS(Orders!$B$2:$B${MAX_ROW},A{i},Orders!$D$2:$D${MAX_ROW},\"<>delivered\","
            f"Orders!$D$2:$D${MAX_ROW},\"<>cancelled\")"
        ))
        col8 = ws_acc.cell(row=i, column=8, value=f"=SUMIFS(Orders!$H$2:$H${MAX_ROW},Orders!$B$2:$B${MAX_ROW},A{i})")
        col8.number_format = CURRENCY_FMT
        ws_acc.cell(row=i, column=9, value=c.created_at.strftime("%Y-%m-%d"))
    last = max(len(customers) + 1, 2)
    _style_body(ws_acc, 2, last, 9)
    _autosize(ws_acc, [24, 11, 14, 8, 10, 9, 12, 14, 12])

    # ---------------- Products ----------------
    ws_prod = wb.create_sheet("Products")
    _write_header(ws_prod, [
        "SKU", "Name", "Origin", "Process", "Roast Level",
        "Wholesale $/Case", "Retail $/Bag", "Cases in Stock", "Bags in Stock",
        "Wholesale $/Bag-Equiv (÷12)", "Retail Markup vs Wholesale",
    ])
    for i, p in enumerate(products, start=2):
        ws_prod.cell(row=i, column=1, value=p.sku)
        ws_prod.cell(row=i, column=2, value=p.name)
        ws_prod.cell(row=i, column=3, value=p.origin)
        ws_prod.cell(row=i, column=4, value=p.process)
        ws_prod.cell(row=i, column=5, value=p.roast_level)
        c6 = ws_prod.cell(row=i, column=6, value=float(p.wholesale_price_per_case))
        c6.number_format = CURRENCY_FMT
        c7 = ws_prod.cell(row=i, column=7, value=float(p.retail_price_per_bag))
        c7.number_format = CURRENCY_FMT
        ws_prod.cell(row=i, column=8, value=p.cases_in_stock)
        ws_prod.cell(row=i, column=9, value=p.bags_in_stock)
        c10 = ws_prod.cell(row=i, column=10, value=f"=F{i}/12")
        c10.number_format = CURRENCY_FMT
        c11 = ws_prod.cell(row=i, column=11, value=f"=IFERROR((G{i}-J{i})/J{i},\"\")")
        c11.number_format = PCT_FMT
    last = max(len(products) + 1, 2)
    _style_body(ws_prod, 2, last, 11)
    ws_prod.cell(row=last + 2, column=1, value="Assumes 12 bags per wholesale case.").font = Font(name="Arial", size=9, italic=True)
    _autosize(ws_prod, [12, 22, 12, 12, 12, 15, 13, 13, 13, 18, 20])

    # ---------------- Green Coffee Lots ----------------
    ws_lots = wb.create_sheet("Green Coffee Lots")
    _write_header(ws_lots, [
        "Lot Code", "Origin", "Farm / Co-op", "Process", "Arrival Date",
        "Received (kg)", "Remaining (kg)", "Cost/kg (USD)", "% Remaining", "Status",
    ])
    for i, lot in enumerate(lots, start=2):
        ws_lots.cell(row=i, column=1, value=lot.lot_code)
        ws_lots.cell(row=i, column=2, value=lot.origin)
        ws_lots.cell(row=i, column=3, value=lot.farm_or_coop)
        ws_lots.cell(row=i, column=4, value=lot.process)
        ws_lots.cell(row=i, column=5, value=lot.arrival_date.strftime("%Y-%m-%d"))
        ws_lots.cell(row=i, column=6, value=float(lot.weight_kg_received))
        ws_lots.cell(row=i, column=7, value=float(lot.weight_kg_remaining))
        c8 = ws_lots.cell(row=i, column=8, value=float(lot.cost_per_kg_usd))
        c8.number_format = CURRENCY_FMT
        c9 = ws_lots.cell(row=i, column=9, value=f"=IFERROR(G{i}/F{i},\"\")")
        c9.number_format = PCT_FMT
        ws_lots.cell(row=i, column=10, value=f"=IF(I{i}<=0.15,\"Low\",\"OK\")")
    last = max(len(lots) + 1, 2)
    _style_body(ws_lots, 2, last, 10)
    _autosize(ws_lots, [12, 12, 22, 12, 13, 13, 15, 13, 12, 9])

    # ---------------- Roast Batches ----------------
    ws_batches = wb.create_sheet("Roast Batches")
    _write_header(ws_batches, [
        "Batch Number", "Product SKU", "Product Name", "Lot Code", "Roast Date",
        "Green (kg)", "Roasted (kg)", "Yield %", "Roasted By", "Notes",
    ])
    for i, b in enumerate(batches, start=2):
        ws_batches.cell(row=i, column=1, value=b.batch_number)
        ws_batches.cell(row=i, column=2, value=b.product.sku)
        ws_batches.cell(row=i, column=3, value=b.product.name)
        ws_batches.cell(row=i, column=4, value=b.lot.lot_code)
        ws_batches.cell(row=i, column=5, value=b.roast_date.strftime("%Y-%m-%d"))
        ws_batches.cell(row=i, column=6, value=float(b.green_weight_kg))
        ws_batches.cell(row=i, column=7, value=float(b.roasted_weight_kg) if b.roasted_weight_kg else None)
        c8 = ws_batches.cell(row=i, column=8, value=f"=IFERROR(G{i}/F{i},\"\")")
        c8.number_format = PCT_FMT
        ws_batches.cell(row=i, column=9, value=b.roasted_by or "")
        ws_batches.cell(row=i, column=10, value=b.notes or "")
    last = max(len(batches) + 1, 2)
    _style_body(ws_batches, 2, last, 10)
    _autosize(ws_batches, [18, 14, 22, 12, 13, 12, 13, 10, 16, 30])

    # ---------------- Subscriptions ----------------
    ws_subs = wb.create_sheet("Subscriptions")
    _write_header(ws_subs, ["Customer", "Product", "Frequency", "Quantity", "Status", "Next Ship Date"])
    for i, s in enumerate(subs, start=2):
        ws_subs.cell(row=i, column=1, value=s.customer.name)
        ws_subs.cell(row=i, column=2, value=s.product.name)
        ws_subs.cell(row=i, column=3, value=s.frequency)
        ws_subs.cell(row=i, column=4, value=s.quantity)
        ws_subs.cell(row=i, column=5, value=s.status)
        ws_subs.cell(row=i, column=6, value=s.next_ship_date.strftime("%Y-%m-%d") if s.next_ship_date else "")
    last = max(len(subs) + 1, 2)
    _style_body(ws_subs, 2, last, 6)
    _autosize(ws_subs, [22, 22, 12, 10, 11, 15])

    wb.active = wb["Orders"]

    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
