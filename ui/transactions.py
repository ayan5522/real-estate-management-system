"""
ui/transactions.py - View and search transactions
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import (COLORS, FONTS, styled_button, card_frame,
                   style_treeview, populate_tree)


class TransactionsModule:
    def __init__(self, parent, session):
        self.parent  = parent
        self.session = session
        self._build_ui()
        self._load_table()

    def _build_ui(self):
        frame = tk.Frame(self.parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        hdr = tk.Frame(frame, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 14))
        tk.Label(hdr, text="Transactions",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")

        # Search
        scard = card_frame(frame, padx=12, pady=10)
        scard.pack(fill="x", pady=(0, 10))
        tk.Label(scard, text="🔍 Search:", font=FONTS["bold"],
                 bg=COLORS["card"]).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._search())
        ttk.Entry(scard, textvariable=self.search_var, width=36).pack(side="left", padx=8)
        styled_button(scard, "Clear", lambda: self.search_var.set(""),
                      bg=COLORS["text_muted"], width=8).pack(side="left")

        # Summary cards
        self.summary_frame = tk.Frame(frame, bg=COLORS["bg"])
        self.summary_frame.pack(fill="x", pady=(0, 10))

        # Table
        tcard = card_frame(frame, padx=0, pady=0)
        tcard.pack(fill="both", expand=True)

        cols = ("ID", "Property", "Client", "Amount (₹)", "Type", "Date", "Notes")
        self.tree = ttk.Treeview(tcard, columns=cols, show="headings", height=18)
        widths = [50, 200, 150, 120, 80, 100, 180]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        style_treeview(self.tree)
        self.tree.tag_configure("Sale", background="#D1FAE5")
        self.tree.tag_configure("Rent", background="#FEF3C7")

        vsb = ttk.Scrollbar(tcard, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        btn_row = tk.Frame(tcard, bg=COLORS["card"], pady=8, padx=8)
        btn_row.pack(fill="x")
        styled_button(btn_row, "🔄 Refresh", self._load_table,
                      bg=COLORS["accent"], width=12).pack(side="right", padx=4)

    def _load_table(self):
        try:
            rows = db.get_all_transactions()
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        self._render(rows)

    def _search(self):
        term = self.search_var.get().strip()
        if not term:
            self._load_table(); return
        try:
            rows = db.search_transactions(term)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        self._render(rows)

    def _render(self, rows):
        # Update summary
        for w in self.summary_frame.winfo_children():
            w.destroy()
        total_rev   = sum(float(r.get("amount", 0) or 0) for r in rows)
        sales_count = sum(1 for r in rows if r.get("type") == "Sale")
        rent_count  = sum(1 for r in rows if r.get("type") == "Rent")
        for icon, label, value, color in [
            ("📦", "Total",       len(rows),          COLORS["accent"]),
            ("💰", "Revenue",     f"₹{total_rev:,.0f}", COLORS["success"]),
            ("🏠", "Sales",       sales_count,         "#7C3AED"),
            ("🏡", "Rentals",     rent_count,          COLORS["warning"]),
        ]:
            c = card_frame(self.summary_frame, padx=16, pady=10)
            c.pack(side="left", padx=6, expand=True, fill="x")
            tk.Label(c, text=f"{icon}  {label}",
                     font=FONTS["bold"], bg=COLORS["card"],
                     fg=COLORS["text_muted"]).pack(anchor="w")
            tk.Label(c, text=str(value),
                     font=("Segoe UI", 18, "bold"),
                     bg=COLORS["card"], fg=color).pack(anchor="w")

        # Populate tree
        self.tree.delete(*self.tree.get_children())
        cols = ("id", "property_title", "client_name", "amount", "type", "date", "notes")
        for i, row in enumerate(rows):
            values = [row.get(c, "") for c in cols]
            tag = row.get("type", "")
            self.tree.insert("", "end", values=values, tags=(tag,))
