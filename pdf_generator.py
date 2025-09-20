#!/usr/bin/env python3
"""
PDF Generator for Happy Buttons simulation.
Generates deterministic, simple PDFs for Orders and Invoices.
Requires: reportlab (pip install reportlab)

Usage:
  python pdf_generator.py --type order --out samples/order_001.pdf
  python pdf_generator.py --type invoice --out samples/invoice_001.pdf
  # With seed for deterministic content:
  python pdf_generator.py --type order --seed 123 --out samples/order_seed123.pdf
"""
import argparse, random, os, datetime, json
from pathlib import Path

def try_import_reportlab():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import mm
        return (True, A4, canvas, mm)
    except Exception as e:
        return (False, None, None, None)

OK, A4, canvas, mm = try_import_reportlab()

def gen_order_payload(seed=None):
    if seed is not None:
        random.seed(seed)
    order_id = f"HB-PO-{random.randint(1000,9999)}"
    items = [
        {"sku":"BTN-4H-FASH-RED-S","desc":"4-hole Fashion Button Red (Small)","qty":random.choice([50,100,200,500])},
        {"sku":"BTN-2H-OEM-WHITE-15","desc":"2-hole OEM Button White 15mm","qty":random.choice([1000,5000,10000])}
    ]
    return {
        "order_id": order_id,
        "customer": {"name":"Alice Co.","email":"alice@example.com"},
        "requested_date": (datetime.date.today()+datetime.timedelta(days=2)).isoformat(),
        "destination": "Magdeburg DC",
        "items": items
    }

def gen_invoice_payload(seed=None):
    if seed is not None:
        random.seed(seed)
    invoice_id = f"HB-INV-{random.randint(1000,9999)}"
    amount = random.choice([199.00, 1299.50, 5599.00])
    return {
        "invoice_id": invoice_id,
        "order_id": f"HB-2025-{random.randint(100000,999999)}",
        "bill_to": "Alice Co., 1 High Street, London",
        "amount": amount,
        "due_date": (datetime.date.today()+datetime.timedelta(days=14)).isoformat(),
        "payment_terms": "Net 14"
    }

def draw_kv(c, x, y, key, value):
    c.setFont("Helvetica-Bold", 11); c.drawString(x, y, f"{key}:")
    c.setFont("Helvetica", 11); c.drawString(x+120, y, str(value))

def write_order_pdf(path, payload):
    if not OK:
        raise RuntimeError("reportlab not available. Install with: pip install reportlab")
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    y = h - 40
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "PURCHASE ORDER")
    y -= 30
    draw_kv(c, 40, y, "Order ID", payload["order_id"]); y-=18
    draw_kv(c, 40, y, "Customer", f"{payload['customer']['name']} <{payload['customer']['email']}>"); y-=18
    draw_kv(c, 40, y, "Requested Date", payload["requested_date"]); y-=18
    draw_kv(c, 40, y, "Destination", payload["destination"]); y-=28
    c.setFont("Helvetica-Bold", 12); c.drawString(40, y, "Items"); y-=16
    c.setFont("Helvetica", 11)
    for it in payload["items"]:
        c.drawString(50, y, f"- {it['sku']}  {it['desc']}  x{it['qty']}")
        y -= 14
    c.showPage(); c.save()

def write_invoice_pdf(path, payload):
    if not OK:
        raise RuntimeError("reportlab not available. Install with: pip install reportlab")
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4
    y = h - 40
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "INVOICE"); y-=30
    draw_kv(c, 40, y, "Invoice ID", payload["invoice_id"]); y-=18
    draw_kv(c, 40, y, "Order ID", payload["order_id"]); y-=18
    draw_kv(c, 40, y, "Bill To", payload["bill_to"]); y-=18
    draw_kv(c, 40, y, "Amount", f"{payload['amount']:.2f} EUR"); y-=18
    draw_kv(c, 40, y, "Due Date", payload["due_date"]); y-=18
    draw_kv(c, 40, y, "Payment Terms", payload["payment_terms"]); y-=18
    c.showPage(); c.save()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", choices=["order","invoice"], required=True)
    ap.add_argument("--out", required=True, help="output PDF path")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    Path(os.path.dirname(args.out)).mkdir(parents=True, exist_ok=True)

    if args.type == "order":
        p = gen_order_payload(args.seed)
        write_order_pdf(args.out, p)
        print(json.dumps({"type":"order","payload":p,"out":args.out}))
    else:
        p = gen_invoice_payload(args.seed)
        write_invoice_pdf(args.out, p)
        print(json.dumps({"type":"invoice","payload":p,"out":args.out}))

if __name__ == "__main__":
    main()
