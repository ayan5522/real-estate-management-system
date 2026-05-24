"""
ui/pdf_generator.py - Generate sale/rent invoices as PDF using reportlab
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import COLORS, FONTS, styled_button, card_frame

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle, HRFlowable)
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False


class PDFGenerator:
    def __init__(self, parent, session):
        self.parent  = parent
        self.session = session
        self._build_ui()
        self._load_transactions()

    def _build_ui(self):
        frame = tk.Frame(self.parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        hdr = tk.Frame(frame, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 14))
        tk.Label(hdr, text="PDF Invoice Generator",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")

        if not RL_AVAILABLE:
            tk.Label(frame,
                     text="⚠️  reportlab not installed.\nRun: pip install reportlab",
                     font=FONTS["heading"], bg=COLORS["bg"],
                     fg=COLORS["warning"]).pack(expand=True)
            return

        main = tk.Frame(frame, bg=COLORS["bg"])
        main.pack(fill="both", expand=True)

        # ── Transaction picker ────────────────────────────────────────────────
        left = card_frame(main, padx=20, pady=20, width=400)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="Select Transaction",
                 font=FONTS["heading"], bg=COLORS["card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 12))

        tk.Label(left, text="🔍 Filter:", font=FONTS["bold"],
                 bg=COLORS["card"]).pack(anchor="w")
        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", lambda *a: self._filter_tx())
        ttk.Entry(left, textvariable=self.filter_var, width=34).pack(anchor="w",
                   ipady=5, pady=(2, 10))

        self.tx_list = tk.Listbox(left, font=FONTS["label"], height=18,
                                   selectmode="single",
                                   bg=COLORS["white"], fg=COLORS["text"],
                                   selectbackground=COLORS["accent"],
                                   selectforeground="white")
        self.tx_list.pack(fill="both", expand=True)
        self.tx_list.bind("<<ListboxSelect>>", self._on_tx_select)

        # ── Preview / Generate ────────────────────────────────────────────────
        right = card_frame(main, padx=20, pady=20)
        right.pack(side="right", fill="both", expand=True, padx=(14, 0))

        tk.Label(right, text="Invoice Preview",
                 font=FONTS["heading"], bg=COLORS["card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 12))

        self.preview_text = tk.Text(right, width=50, height=22,
                                     font=("Courier New", 9),
                                     bg="#F8FAFC", fg=COLORS["text"],
                                     relief="flat", state="disabled")
        self.preview_text.pack(fill="both", expand=True)

        btn_row = tk.Frame(right, bg=COLORS["card"], pady=10)
        btn_row.pack(fill="x")
        styled_button(btn_row, "📄 Generate PDF",
                      self._generate_pdf, bg=COLORS["success"], width=18).pack(side="left", padx=(0, 8))
        styled_button(btn_row, "🔄 Refresh",
                      self._load_transactions, bg=COLORS["accent"], width=12).pack(side="left")

        self._all_transactions = []
        self._selected_tx = None

    def _load_transactions(self):
        try:
            self._all_transactions = db.get_all_transactions()
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        self._populate_list(self._all_transactions)

    def _populate_list(self, rows):
        self.tx_list.delete(0, "end")
        for row in rows:
            label = (f"#{row['id']}  |  {row.get('property_title','N/A')}  "
                     f"|  {row['client_name']}  |  ₹{float(row['amount']):,.0f}  "
                     f"|  {row['type']}  |  {row['date']}")
            self.tx_list.insert("end", label)

    def _filter_tx(self):
        term = self.filter_var.get().lower()
        if not term:
            self._populate_list(self._all_transactions); return
        filtered = [r for r in self._all_transactions
                    if term in str(r.get("property_title","")).lower()
                    or term in str(r.get("client_name","")).lower()
                    or term in str(r.get("type","")).lower()]
        self._populate_list(filtered)

    def _on_tx_select(self, _):
        sel = self.tx_list.curselection()
        if not sel: return
        idx = sel[0]
        term = self.filter_var.get().lower()
        if term:
            source = [r for r in self._all_transactions
                      if term in str(r.get("property_title","")).lower()
                      or term in str(r.get("client_name","")).lower()
                      or term in str(r.get("type","")).lower()]
        else:
            source = self._all_transactions
        if idx < len(source):
            self._selected_tx = source[idx]
            self._show_preview(self._selected_tx)

    def _show_preview(self, tx):
        try:
            prop = db.get_property_by_id(tx["property_id"]) if tx.get("property_id") else {}
        except Exception:
            prop = {}

        lines = [
            "═" * 54,
            "            REAL ESTATE MANAGEMENT SYSTEM",
            "                     INVOICE",
            "═" * 54,
            f"  Invoice No  : RE-{tx['id']:04d}",
            f"  Date        : {tx['date']}",
            f"  Type        : {tx['type']}",
            "─" * 54,
            "  PROPERTY DETAILS",
            "─" * 54,
            f"  Title       : {prop.get('title', 'N/A')}",
            f"  Location    : {prop.get('location', 'N/A')}",
            f"  Type        : {prop.get('type', 'N/A')}",
            f"  Size        : {prop.get('size', 'N/A')}",
            "─" * 54,
            "  CLIENT DETAILS",
            "─" * 54,
            f"  Client Name : {tx['client_name']}",
            "─" * 54,
            "  PAYMENT DETAILS",
            "─" * 54,
            f"  Amount      : ₹{float(tx['amount']):,.2f}",
            f"  Transaction : {tx['type']}",
            f"  Notes       : {tx.get('notes','') or '—'}",
            "═" * 54,
            "  Thank you for choosing our services!",
            "═" * 54,
        ]

        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", "\n".join(lines))
        self.preview_text.config(state="disabled")

    def _generate_pdf(self):
        if not self._selected_tx:
            messagebox.showwarning("Select", "Please select a transaction first.")
            return

        tx = self._selected_tx
        try:
            prop = db.get_property_by_id(tx["property_id"]) if tx.get("property_id") else {}
        except Exception:
            prop = {}

        default_name = f"Invoice_RE{tx['id']:04d}_{tx['client_name'].replace(' ','_')}.pdf"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF Files", "*.pdf")],
            title="Save Invoice PDF"
        )
        if not save_path: return

        try:
            self._build_pdf(save_path, tx, prop)
            messagebox.showinfo("Success", f"Invoice saved:\n{save_path}")
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))

    def _build_pdf(self, path, tx, prop):
        doc = SimpleDocTemplate(path, pagesize=A4,
                                 leftMargin=20*mm, rightMargin=20*mm,
                                 topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        story  = []

        # Header
        header_style = ParagraphStyle("header",
            fontSize=18, fontName="Helvetica-Bold",
            textColor=rl_colors.HexColor("#1E3A5F"),
            alignment=1, spaceAfter=4)
        sub_style = ParagraphStyle("sub",
            fontSize=11, fontName="Helvetica",
            textColor=rl_colors.HexColor("#64748B"),
            alignment=1, spaceAfter=12)
        story.append(Paragraph("🏠 Real Estate Management System", header_style))
        story.append(Paragraph("OFFICIAL INVOICE", sub_style))
        story.append(HRFlowable(width="100%", thickness=2,
                                 color=rl_colors.HexColor("#1E3A5F")))
        story.append(Spacer(1, 8*mm))

        label_style  = ParagraphStyle("lbl",  fontSize=9, fontName="Helvetica-Bold")
        value_style  = ParagraphStyle("val",  fontSize=9, fontName="Helvetica")
        section_style= ParagraphStyle("sect", fontSize=11, fontName="Helvetica-Bold",
                                       textColor=rl_colors.HexColor("#1E3A5F"),
                                       spaceAfter=4)

        # Invoice meta
        story.append(Paragraph("Invoice Details", section_style))
        meta_data = [
            ["Invoice No",  f"RE-{tx['id']:04d}",
             "Date",        str(tx['date'])],
            ["Type",        tx['type'],
             "Status",      "COMPLETED"],
        ]
        meta_table = Table(meta_data, colWidths=[35*mm, 55*mm, 35*mm, 55*mm])
        meta_table.setStyle(TableStyle([
            ("FONTNAME",    (0,0),(-1,-1), "Helvetica"),
            ("FONTSIZE",    (0,0),(-1,-1), 9),
            ("FONTNAME",    (0,0),(0,-1),  "Helvetica-Bold"),
            ("FONTNAME",    (2,0),(2,-1),  "Helvetica-Bold"),
            ("BACKGROUND",  (0,0),(-1,-1), rl_colors.HexColor("#F8FAFC")),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[rl_colors.HexColor("#F8FAFC"),
                                              rl_colors.white]),
            ("GRID",        (0,0),(-1,-1), 0.5, rl_colors.HexColor("#E2E8F0")),
            ("PADDING",     (0,0),(-1,-1), 6),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 6*mm))

        # Property details
        story.append(Paragraph("Property Details", section_style))
        prop_data = [
            ["Title",       prop.get("title","N/A")],
            ["Type",        prop.get("type","N/A")],
            ["Location",    prop.get("location","N/A")],
            ["Size",        prop.get("size","N/A") or "N/A"],
            ["Description", (prop.get("description","") or "")[:80]],
        ]
        prop_table = Table(prop_data, colWidths=[40*mm, 135*mm])
        prop_table.setStyle(TableStyle([
            ("FONTNAME",  (0,0),(0,-1), "Helvetica-Bold"),
            ("FONTNAME",  (1,0),(1,-1), "Helvetica"),
            ("FONTSIZE",  (0,0),(-1,-1), 9),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),
             [rl_colors.HexColor("#F8FAFC"), rl_colors.white]),
            ("GRID",      (0,0),(-1,-1), 0.5, rl_colors.HexColor("#E2E8F0")),
            ("PADDING",   (0,0),(-1,-1), 6),
        ]))
        story.append(prop_table)
        story.append(Spacer(1, 6*mm))

        # Client details
        story.append(Paragraph("Client Details", section_style))
        client_data = [["Client Name", tx["client_name"]]]
        ct = Table(client_data, colWidths=[40*mm, 135*mm])
        ct.setStyle(TableStyle([
            ("FONTNAME",  (0,0),(0,-1), "Helvetica-Bold"),
            ("FONTNAME",  (1,0),(1,-1), "Helvetica"),
            ("FONTSIZE",  (0,0),(-1,-1), 9),
            ("BACKGROUND",(0,0),(-1,-1), rl_colors.HexColor("#F8FAFC")),
            ("GRID",      (0,0),(-1,-1), 0.5, rl_colors.HexColor("#E2E8F0")),
            ("PADDING",   (0,0),(-1,-1), 6),
        ]))
        story.append(ct)
        story.append(Spacer(1, 6*mm))

        # Amount
        story.append(Paragraph("Payment Summary", section_style))
        amount_data = [
            ["Transaction Type", tx["type"]],
            ["Amount",           f"₹ {float(tx['amount']):,.2f}"],
            ["Notes",            tx.get("notes","") or "—"],
        ]
        at = Table(amount_data, colWidths=[40*mm, 135*mm])
        at.setStyle(TableStyle([
            ("FONTNAME",    (0,0),(0,-1), "Helvetica-Bold"),
            ("FONTNAME",    (1,0),(1,-1), "Helvetica"),
            ("FONTSIZE",    (0,0),(-1,-1), 10),
            ("FONTSIZE",    (1,1),(1,1),   14),
            ("TEXTCOLOR",   (1,1),(1,1),   rl_colors.HexColor("#16A34A")),
            ("FONTNAME",    (1,1),(1,1),   "Helvetica-Bold"),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),
             [rl_colors.HexColor("#F8FAFC"), rl_colors.HexColor("#D1FAE5"),
              rl_colors.white]),
            ("GRID",        (0,0),(-1,-1), 0.5, rl_colors.HexColor("#E2E8F0")),
            ("PADDING",     (0,0),(-1,-1), 8),
        ]))
        story.append(at)
        story.append(Spacer(1, 10*mm))

        # Footer
        story.append(HRFlowable(width="100%", thickness=1,
                                 color=rl_colors.HexColor("#CBD5E1")))
        footer_style = ParagraphStyle("ft", fontSize=8,
                                       textColor=rl_colors.HexColor("#64748B"),
                                       alignment=1, spaceBefore=6)
        story.append(Paragraph(
            "This is a computer-generated invoice. No signature required.<br/>"
            f"Generated on {datetime.datetime.now().strftime('%d %b %Y %H:%M')}  |  "
            "Real Estate Management System",
            footer_style))

        doc.build(story)
