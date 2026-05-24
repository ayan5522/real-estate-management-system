"""
ui/user_management.py - Add / View / Edit / Delete users
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import (COLORS, FONTS, styled_button, card_frame,
                   style_treeview, populate_tree, validate_email)


class UserManagement:
    def __init__(self, parent, session):
        self.parent      = parent
        self.session     = session
        self.selected_id = None
        # Initialise all attributes that methods reference BEFORE _build_ui runs
        self.vars       = {}
        self.role_var   = None
        self.form_title = None
        self.tree       = None
        self._build_ui()
        self._load_table()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        frame = tk.Frame(self.parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header row — button is added at the END (after form is built)
        hdr = tk.Frame(frame, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 16))
        tk.Label(hdr, text="User Management",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")

        # Two-column body
        body = tk.Frame(frame, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)

        # Left: table
        table_card = card_frame(body, padx=0, pady=0)
        table_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._build_table(table_card)

        # Right: form  (self.vars and self.tree are now set)
        form_card = card_frame(body, padx=20, pady=20, width=340)
        form_card.pack(side="right", fill="y")
        form_card.pack_propagate(False)
        self._build_form(form_card)

        # NOW safe to wire the header button
        styled_button(hdr, "➕ Add User", self._show_add_form,
                      bg=COLORS["accent"]).pack(side="right")

    # ── Table ────────────────────────────────────────────────────────────────
    def _build_table(self, parent):
        srow = tk.Frame(parent, bg=COLORS["card"], pady=10, padx=12)
        srow.pack(fill="x")
        tk.Label(srow, text="🔍 Search:", font=FONTS["bold"],
                 bg=COLORS["card"]).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self._search())
        ttk.Entry(srow, textvariable=self.search_var, width=30).pack(side="left", padx=8)
        styled_button(srow, "Clear", lambda: self.search_var.set(""),
                      bg=COLORS["text_muted"], width=8).pack(side="left")

        tree_cols = ("ID", "Name", "Username", "Email", "Contact", "Role")
        self.tree = ttk.Treeview(parent, columns=tree_cols, show="headings", height=18)
        for c in tree_cols:
            w = 60 if c == "ID" else 140
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
        styled_button(btn_row, "🔄 Refresh", self._load_table,      bg=COLORS["accent"],  width=10).pack(side="right", padx=4)

    # ── Form ─────────────────────────────────────────────────────────────────
    def _build_form(self, parent):
        self.form_title = tk.Label(parent, text="Add New User",
                                   font=FONTS["heading"],
                                   bg=COLORS["card"], fg=COLORS["text"])
        self.form_title.pack(anchor="w", pady=(0, 16))

        self.vars = {}
        for label, key in [("Full Name *", "name"), ("Username *", "username"),
                             ("Password *",  "password"), ("Email", "email"),
                             ("Contact",     "contact")]:
            tk.Label(parent, text=label, font=FONTS["bold"],
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            v = tk.StringVar()
            ttk.Entry(parent, textvariable=v, width=32,
                      show="●" if key == "password" else "").pack(
                anchor="w", ipady=5, pady=(2, 10))
            self.vars[key] = v

        tk.Label(parent, text="Role *", font=FONTS["bold"],
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        self.role_var = tk.StringVar(value="agent")
        ttk.Combobox(parent, textvariable=self.role_var,
                     values=["admin", "agent"], state="readonly",
                     width=30).pack(anchor="w", ipady=5, pady=(2, 16))

        btn_row = tk.Frame(parent, bg=COLORS["card"])
        btn_row.pack(fill="x")
        styled_button(btn_row, "💾 Save",  self._save_user,
                      bg=COLORS["success"],    width=12).pack(side="left", padx=(0, 8))
        styled_button(btn_row, "🧹 Clear", self._clear_form,
                      bg=COLORS["text_muted"], width=10).pack(side="left")

    # ── Data operations ───────────────────────────────────────────────────────
    def _show_add_form(self):
        """Reset the form panel for a new user (called only after UI is built)."""
        self._clear_form()

    def _load_table(self):
        try:
            users = db.get_all_users()
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        populate_tree(self.tree, users,
                      ("id", "name", "username", "email", "contact", "role"))

    def _search(self):
        term = self.search_var.get().strip()
        if not term:
            self._load_table(); return
        try:
            users = db.search_users(term)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        populate_tree(self.tree, users,
                      ("id", "name", "username", "email", "contact", "role"))

    def _on_select(self, _event):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0], "values")[0]

    def _edit_selected(self):
        if not self.selected_id:
            messagebox.showwarning("Select Row", "Please select a user first."); return
        try:
            user = db.get_user_by_id(self.selected_id)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        if not user: return
        self.form_title.config(text="Edit User")
        self.vars["name"].set(user["name"])
        self.vars["username"].set(user["username"])
        self.vars["password"].set("")
        self.vars["email"].set(user["email"] or "")
        self.vars["contact"].set(user["contact"] or "")
        self.role_var.set(user["role"])

    def _save_user(self):
        name     = self.vars["name"].get().strip()
        username = self.vars["username"].get().strip()
        password = self.vars["password"].get().strip()
        email    = self.vars["email"].get().strip()
        contact  = self.vars["contact"].get().strip()
        role     = self.role_var.get()

        if not name or not username:
            messagebox.showwarning("Validation", "Name and Username are required."); return
        if email and not validate_email(email):
            messagebox.showwarning("Validation", "Invalid email address."); return

        try:
            if self.selected_id and self.form_title.cget("text") == "Edit User":
                db.update_user(self.selected_id, name, email, contact, role,
                               password if password else None)
                messagebox.showinfo("Success", "User updated successfully.")
            else:
                if not password:
                    messagebox.showwarning("Validation", "Password is required for new users."); return
                db.add_user(name, username, password, email, contact, role)
                messagebox.showinfo("Success", "User added successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        self._clear_form()
        self._load_table()

    def _delete_selected(self):
        if not self.selected_id:
            messagebox.showwarning("Select Row", "Please select a user first."); return
        if self.selected_id == str(self.session.get("id")):
            messagebox.showwarning("Not Allowed", "You cannot delete your own account."); return
        if messagebox.askyesno("Confirm Delete", "Delete this user permanently?"):
            try:
                db.delete_user(self.selected_id)
            except Exception as e:
                messagebox.showerror("Error", str(e)); return
            self.selected_id = None
            self._load_table()

    def _clear_form(self):
        if self.vars:
            for v in self.vars.values():
                v.set("")
        if self.role_var:
            self.role_var.set("agent")
        if self.form_title:
            self.form_title.config(text="Add New User")
        self.selected_id = None
