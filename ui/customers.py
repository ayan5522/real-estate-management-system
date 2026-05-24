"""
ui/customers.py - Customer CRUD + purchase history tracking
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import (COLORS, FONTS, styled_button, card_frame,
                   style_treeview, populate_tree, validate_email)


class CustomersModule:
    def __init__(self, parent, session):
        self.parent      = parent
        self.session     = session
        self.selected_id = None
        # Pre-declare so _clear_form / _show_form are safe to call at any time
        self.vars           = {}
        self.form_title_lbl = None
        self.tree           = None
        self._build_ui()
        self._load_table()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        frame = tk.Frame(self.parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header row — button added AFTER form is built
        hdr = tk.Frame(frame, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 14))
        tk.Label(hdr, text="Customer Management",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")

        # Body
        body = tk.Frame(frame, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)

        # Left: table
        tcard = card_frame(body, padx=0, pady=0)
        tcard.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._build_table(tcard)

        # Right: form  (self.vars / self.tree now set)
        fcard = card_frame(body, padx=20, pady=20, width=320)
        fcard.pack(side="right", fill="y")
        fcard.pack_propagate(False)
        self._build_form(fcard)

        # NOW safe to wire the header button
        styled_button(hdr, "➕ Add Customer", self._show_form,
                      bg=COLORS["accent"]).pack(side="right")

    # ── Table ────────────────────────────────────────────────────────────────
    def _build_table(self, parent):
        srow = tk.Frame(parent, bg=COLORS["card"], pady=10, padx=12)
        srow.pack(fill="x")
        tk.Label(srow, text="🔍", font=FONTS["label"],
                 bg=COLORS["card"]).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._search())
        ttk.Entry(srow, textvariable=self.search_var, width=30).pack(side="left", padx=6)
        styled_button(srow, "Clear", lambda: self.search_var.set(""),
                      bg=COLORS["text_muted"], width=8).pack(side="left")

        tree_cols = ("ID", "Name", "Contact", "Email", "Address", "Added")
        self.tree = ttk.Treeview(parent, columns=tree_cols, show="headings", height=16)
        widths = [50, 150, 120, 170, 160, 100]
        for c, w in zip(tree_cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        style_treeview(self.tree)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        btn_row = tk.Frame(parent, bg=COLORS["card"], pady=8, padx=8)
        btn_row.pack(fill="x")
        styled_button(btn_row, "✏️ Edit",    self._edit_selected,   bg=COLORS["warning"], width=10).pack(side="left", padx=4)
        styled_button(btn_row, "🗑️ Delete",  self._delete_selected, bg=COLORS["danger"],  width=10).pack(side="left", padx=4)
        styled_button(btn_row, "📋 History", self._view_history,    bg="#7C3AED",          width=12).pack(side="left", padx=4)
        styled_button(btn_row, "🔄 Refresh", self._load_table,      bg=COLORS["accent"],   width=10).pack(side="right", padx=4)

    # ── Form ─────────────────────────────────────────────────────────────────
    def _build_form(self, parent):
        self.form_title_lbl = tk.Label(parent, text="Add Customer",
                                       font=FONTS["heading"],
                                       bg=COLORS["card"], fg=COLORS["text"])
        self.form_title_lbl.pack(anchor="w", pady=(0, 14))

        self.vars = {}
        for label, key in [("Name *",  "name"), ("Contact", "contact"),
                             ("Email",   "email"), ("Address", "address")]:
            tk.Label(parent, text=label, font=FONTS["bold"],
                     bg=COLORS["card"]).pack(anchor="w")
            v = tk.StringVar()
            ttk.Entry(parent, textvariable=v, width=30).pack(
                anchor="w", ipady=5, pady=(2, 10))
            self.vars[key] = v

        brow = tk.Frame(parent, bg=COLORS["card"])
        brow.pack(fill="x", pady=4)
        styled_button(brow, "💾 Save",  self._save,
                      bg=COLORS["success"],    width=12).pack(side="left", padx=(0, 6))
        styled_button(brow, "🧹 Clear", self._clear_form,
                      bg=COLORS["text_muted"], width=10).pack(side="left")

    # ── Data operations ───────────────────────────────────────────────────────
    def _show_form(self):
        """Reset form for new customer (only called after UI is fully built)."""
        self._clear_form()

    def _load_table(self):
        try:
            rows = db.get_all_customers()
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        populate_tree(self.tree, rows,
                      ("id", "name", "contact", "email", "address", "created_at"))

    def _search(self):
        term = self.search_var.get().strip()
        if not term:
            self._load_table(); return
        try:
            rows = db.search_customers(term)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        populate_tree(self.tree, rows,
                      ("id", "name", "contact", "email", "address", "created_at"))

    def _on_select(self, _event):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0], "values")[0]

    def _edit_selected(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select a customer first."); return
        values = self.tree.item(self.tree.selection()[0], "values")
        self.form_title_lbl.config(text="Edit Customer")
        self.vars["name"].set(values[1])
        self.vars["contact"].set(values[2])
        self.vars["email"].set(values[3])
        self.vars["address"].set(values[4])

    def _save(self):
        name    = self.vars["name"].get().strip()
        contact = self.vars["contact"].get().strip()
        email   = self.vars["email"].get().strip()
        address = self.vars["address"].get().strip()
        if not name:
            messagebox.showwarning("Validation", "Name is required."); return
        if email and not validate_email(email):
            messagebox.showwarning("Validation", "Invalid email."); return
        try:
            if self.selected_id and self.form_title_lbl.cget("text") == "Edit Customer":
                db.update_customer(self.selected_id, name, contact, email, address)
                messagebox.showinfo("Success", "Customer updated.")
            else:
                db.add_customer(name, contact, email, address)
                messagebox.showinfo("Success", "Customer added.")
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        self._clear_form()
        self._load_table()

    def _delete_selected(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select a customer first."); return
        if messagebox.askyesno("Confirm", "Delete this customer?"):
            try:
                db.delete_customer(self.selected_id)
            except Exception as e:
                messagebox.showerror("Error", str(e)); return
            self.selected_id = None
            self._load_table()

    def _view_history(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select a customer first."); return
        values = self.tree.item(self.tree.selection()[0], "values")
        client_name = values[1]
        try:
            rows = db.execute_query("""
                SELECT t.*, p.title AS property_title
                FROM transactions t
                LEFT JOIN properties p ON t.property_id = p.id
                WHERE t.client_name = %s
                ORDER BY t.date DESC
            """, (client_name,), fetch=True)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        win = tk.Toplevel(self.parent)
        win.title(f"Purchase History – {client_name}")
        win.geometry("700x400")
        win.configure(bg=COLORS["bg"])
        win.grab_set()

        tk.Label(win, text=f"History for: {client_name}",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(pady=10)

        hist_cols = ("ID", "Property", "Amount (₹)", "Type", "Date")
        tree = ttk.Treeview(win, columns=hist_cols, show="headings", height=12)
        for c in hist_cols:
            tree.heading(c, text=c)
            tree.column(c, width=130, anchor="center")
        style_treeview(tree)
        tree.pack(fill="both", expand=True, padx=20)
        populate_tree(tree, rows,
                      ("id", "property_title", "amount", "type", "date"))

        if not rows:
            tk.Label(win, text="No transactions found for this customer.",
                     font=FONTS["label"], bg=COLORS["bg"],
                     fg=COLORS["text_muted"]).pack(pady=10)

    def _clear_form(self):
        if self.vars:
            for v in self.vars.values():
                v.set("")
        if self.form_title_lbl:
            self.form_title_lbl.config(text="Add Customer")
        self.selected_id = None
