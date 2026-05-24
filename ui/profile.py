"""
ui/profile.py - User profile view/edit
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import COLORS, FONTS, styled_button, card_frame, validate_email


class ProfilePage:
    def __init__(self, parent, session, on_update=None):
        self.parent    = parent
        self.session   = session
        self.on_update = on_update
        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self.parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="My Profile",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 20))

        card = card_frame(frame, padx=28, pady=28, width=480)
        card.pack(anchor="nw")
        card.pack_propagate(False)

        # Avatar
        av_frame = tk.Frame(card, bg=COLORS["card"])
        av_frame.pack(pady=(0, 20))
        av = tk.Label(av_frame, text="👤",
                      font=("Segoe UI", 48), bg=COLORS["accent"],
                      fg="white", width=3, pady=8)
        av.pack()
        role_badge = tk.Label(av_frame,
                              text=self.session.get("role","").upper(),
                              font=("Segoe UI", 9, "bold"),
                              bg=COLORS["success"] if self.session.get("role") == "admin" else COLORS["warning"],
                              fg="white", padx=10, pady=3)
        role_badge.pack(pady=4)

        self.vars = {}
        user = db.get_user_by_id(self.session["id"])
        for label, key, editable in [
            ("Full Name",  "name",     True),
            ("Username",   "username", False),
            ("Email",      "email",    True),
            ("Contact",    "contact",  True),
            ("Role",       "role",     False),
        ]:
            row = tk.Frame(card, bg=COLORS["card"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{label}:", font=FONTS["bold"],
                     bg=COLORS["card"], width=12, anchor="w").pack(side="left")
            v = tk.StringVar(value=user.get(key, "") or "")
            state = "normal" if editable else "disabled"
            e = ttk.Entry(row, textvariable=v, width=30, state=state)
            e.pack(side="left", ipady=4, padx=6)
            self.vars[key] = v

        # Change password section
        sep = tk.Frame(card, bg=COLORS["border"], height=1)
        sep.pack(fill="x", pady=12)
        tk.Label(card, text="Change Password (leave blank to keep current)",
                 font=FONTS["small"], bg=COLORS["card"],
                 fg=COLORS["text_muted"]).pack(anchor="w")
        pw_var = tk.StringVar()
        ttk.Entry(card, textvariable=pw_var, show="●", width=34).pack(
            anchor="w", ipady=5, pady=(4, 12))
        self.vars["new_password"] = pw_var

        def save():
            name    = self.vars["name"].get().strip()
            email   = self.vars["email"].get().strip()
            contact = self.vars["contact"].get().strip()
            new_pw  = self.vars["new_password"].get().strip()
            role    = self.vars["role"].get()

            if not name:
                messagebox.showwarning("Validation", "Name is required."); return
            if email and not validate_email(email):
                messagebox.showwarning("Validation", "Invalid email."); return
            try:
                db.update_user(self.session["id"], name, email, contact, role,
                               new_pw if new_pw else None)
                self.session["name"] = name
                messagebox.showinfo("Success", "Profile updated successfully.")
                if self.on_update:
                    self.on_update(self.session)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        styled_button(card, "💾 Save Changes", save,
                      bg=COLORS["success"], width=18).pack(anchor="w")
