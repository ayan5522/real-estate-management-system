"""
ui/agent_dashboard.py - Agent dashboard (subset of admin capabilities)
"""

import tkinter as tk
from tkinter import messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import COLORS, FONTS, card_frame


class AgentDashboard:
    def __init__(self, root, session_user, on_logout):
        self.root = root
        self.session = session_user
        self.on_logout = on_logout
        self.current_module = None
        self._build_layout()
        self._show_home()

    def _build_layout(self):
        self.root.title(f"Agent Dashboard  –  {self.session['name']}")
        self.root.resizable(True, True)
        try:
            self.root.state("zoomed")
        except Exception:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.configure(bg=COLORS["bg"])

        outer = tk.Frame(self.root, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(outer, bg=COLORS["sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        self.content = tk.Frame(outer, bg=COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True)

    def _build_sidebar(self):
        sb = self.sidebar
        tk.Label(sb, text="🏠  RE Manager",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["sidebar"], fg="white", pady=18).pack(fill="x", padx=10)

        badge = tk.Frame(sb, bg=COLORS["sidebar_btn"], pady=10)
        badge.pack(fill="x", padx=10, pady=10)
        tk.Label(badge, text="👤", font=("Segoe UI", 20),
                 bg=COLORS["sidebar_btn"], fg=COLORS["success"]).pack()
        tk.Label(badge, text=self.session["name"],
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["sidebar_btn"], fg="white").pack()
        tk.Label(badge, text="Agent",
                 font=("Segoe UI", 8),
                 bg=COLORS["sidebar_btn"], fg="#94A3B8").pack()

        nav_items = [
            ("🏠  Home",           "home"),
            ("🏘️  Properties",     "properties"),
            ("💰  Transactions",   "transactions"),
            ("👤  Customers",      "customers"),
            ("📅  Appointments",   "appointments"),
            ("🧮  EMI Calculator", "emi"),
            ("📄  PDF Generator",  "pdf"),
        ]
        self._nav_buttons = {}
        for label, key in nav_items:
            btn = tk.Button(sb, text=label,
                            command=lambda k=key: self._navigate(k),
                            bg=COLORS["sidebar_btn"], fg="white",
                            font=FONTS["sidebar"], relief="flat",
                            anchor="w", padx=18, pady=10, cursor="hand2")
            btn.pack(fill="x", pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLORS["sidebar_hover"]))
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.config(
                bg=COLORS["accent"] if self.current_module == k else COLORS["sidebar_btn"]))
            self._nav_buttons[key] = btn

        tk.Frame(sb, bg=COLORS["sidebar"]).pack(fill="both", expand=True)
        tk.Button(sb, text="🚪  Logout", command=self._logout,
                  bg="#7F1D1D", fg="white", font=FONTS["sidebar"],
                  relief="flat", anchor="w", padx=18, pady=10,
                  cursor="hand2").pack(fill="x")

    def _navigate(self, key):
        for k, b in self._nav_buttons.items():
            b.config(bg=COLORS["sidebar_btn"])
        if key in self._nav_buttons:
            self._nav_buttons[key].config(bg=COLORS["accent"])
        self.current_module = key
        for w in self.content.winfo_children():
            w.destroy()

        if   key == "home":        self._show_home()
        elif key == "properties":  self._load_properties()
        elif key == "transactions":self._load_transactions()
        elif key == "customers":   self._load_customers()
        elif key == "appointments":self._load_appointments()
        elif key == "emi":         self._load_emi()
        elif key == "pdf":         self._load_pdf()

    def _show_home(self):
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(frame, text="Agent Dashboard",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 20))

        try:
            summary = db.get_dashboard_summary()
        except Exception:
            summary = {"properties": "-", "transactions": "-", "revenue": "-",
                       "pending_appointments": "-"}

        cards = [
            ("🏘️", "Properties",      summary["properties"],              COLORS["accent"]),
            ("💰", "Transactions",     summary["transactions"],            "#7C3AED"),
            ("💵", "Revenue",          f"₹{float(summary['revenue'] or 0):,.0f}", "#D97706"),
            ("📅", "Pending Appts",    summary["pending_appointments"],    COLORS["danger"]),
        ]
        row = tk.Frame(frame, bg=COLORS["bg"])
        row.pack(fill="x", pady=(0, 20))
        for icon, label, value, color in cards:
            c = card_frame(row, padx=20, pady=20)
            c.pack(side="left", padx=8, expand=True, fill="x")
            tk.Label(c, text=icon, font=("Segoe UI", 28),
                     bg=COLORS["card"]).pack()
            tk.Label(c, text=str(value), font=FONTS["card_num"],
                     bg=COLORS["card"], fg=color).pack()
            tk.Label(c, text=label, font=FONTS["small"],
                     bg=COLORS["card"], fg=COLORS["text_muted"]).pack()

        tk.Label(frame, text="Quick Actions",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(10, 8))
        qa = tk.Frame(frame, bg=COLORS["bg"])
        qa.pack(fill="x")
        for txt, nav, color in [
            ("➕ Add Property",   "properties", COLORS["accent"]),
            ("📅 Appointments",  "appointments", COLORS["success"]),
            ("🧮 EMI Calc",       "emi",         "#D97706"),
        ]:
            tk.Button(qa, text=txt, command=lambda k=nav: self._navigate(k),
                      bg=color, fg="white", font=FONTS["btn"],
                      relief="flat", padx=18, pady=10,
                      cursor="hand2").pack(side="left", padx=6)

    def _load_properties(self):
        from ui.property_management import PropertyManagement
        PropertyManagement(self.content, self.session)

    def _load_transactions(self):
        from ui.transactions import TransactionsModule
        TransactionsModule(self.content, self.session)

    def _load_customers(self):
        from ui.customers import CustomersModule
        CustomersModule(self.content, self.session)

    def _load_appointments(self):
        from ui.appointments import AppointmentsModule
        AppointmentsModule(self.content, self.session)

    def _load_emi(self):
        from ui.emi_calculator import EMICalculator
        EMICalculator(self.content)

    def _load_pdf(self):
        from ui.pdf_generator import PDFGenerator
        PDFGenerator(self.content, self.session)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.on_logout()
