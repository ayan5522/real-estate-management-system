"""
ui/admin_dashboard.py - Admin dashboard with sidebar and module switcher
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import COLORS, FONTS, card_frame


class AdminDashboard:
    def __init__(self, root, session_user, on_logout):
        self.root = root
        self.session = session_user   # dict with user info
        self.on_logout = on_logout
        self.current_module = None
        self._build_layout()
        self._show_home()

    # ── Main layout ───────────────────────────────────────────────────────────
    def _build_layout(self):
        self.root.title(f"Admin Dashboard  –  {self.session['name']}")
        self.root.resizable(True, True)
        # Open maximised; fall back to full-screen geometry if state() not supported
        try:
            self.root.state("zoomed")
        except Exception:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.configure(bg=COLORS["bg"])

        # Outer pane
        outer = tk.Frame(self.root, bg=COLORS["bg"])
        outer.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(outer, bg=COLORS["sidebar"], width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Content area
        self.content = tk.Frame(outer, bg=COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True)

    def _build_sidebar(self):
        sb = self.sidebar

        # Logo area
        tk.Label(sb, text="🏠  RE Manager",
                 font=("Segoe UI", 13, "bold"),
                 bg=COLORS["sidebar"], fg="white",
                 pady=18).pack(fill="x", padx=10)
        ttk.Separator(sb, orient="horizontal").pack(fill="x", padx=10)

        # User badge
        badge = tk.Frame(sb, bg=COLORS["sidebar_btn"], pady=10)
        badge.pack(fill="x", padx=10, pady=10)
        tk.Label(badge, text="👤", font=("Segoe UI", 20),
                 bg=COLORS["sidebar_btn"], fg=COLORS["accent"]).pack()
        tk.Label(badge, text=self.session["name"],
                 font=("Segoe UI", 10, "bold"),
                 bg=COLORS["sidebar_btn"], fg="white").pack()
        tk.Label(badge, text="Administrator",
                 font=("Segoe UI", 8),
                 bg=COLORS["sidebar_btn"], fg="#94A3B8").pack()

        # Nav buttons
        nav_items = [
            ("🏠    Home",             "home"),
            ("👥    Users",            "users"),
            ("🏘  Properties",   "properties"),
            ("💰    Transactions",     "transactions"),
            ("👤    Customers",        "customers"),
            ("📅    Appointments",     "appointments"),
            ("📊    Analytics",        "analytics"),
            ("🧮    EMI Calculator",   "emi"),
            ("📄    PDF Generator",    "pdf"),
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

        # Logout at bottom
        tk.Frame(sb, bg=COLORS["sidebar"]).pack(fill="both", expand=True)
        tk.Button(sb, text="🚪  Logout",
                  command=self._logout,
                  bg="#7F1D1D", fg="white",
                  font=FONTS["sidebar"], relief="flat",
                  anchor="w", padx=18, pady=10, cursor="hand2").pack(fill="x")

    def _navigate(self, key):
        # Reset all sidebar button colours
        for k, b in self._nav_buttons.items():
            b.config(bg=COLORS["sidebar_btn"])
        self._nav_buttons[key].config(bg=COLORS["accent"])
        self.current_module = key

        # Clear content
        for w in self.content.winfo_children():
            w.destroy()

        # Route
        if   key == "home":        self._show_home()
        elif key == "users":       self._load_users()
        elif key == "properties":  self._load_properties()
        elif key == "transactions":self._load_transactions()
        elif key == "customers":   self._load_customers()
        elif key == "appointments":self._load_appointments()
        elif key == "analytics":   self._load_analytics()
        elif key == "emi":         self._load_emi()
        elif key == "pdf":         self._load_pdf()

    # ── Home / Summary ────────────────────────────────────────────────────────
    def _show_home(self):
        frame = tk.Frame(self.content, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        # Header
        hdr = tk.Frame(frame, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 20))
        tk.Label(hdr, text="Dashboard Overview",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")
        tk.Label(hdr, text=f"Welcome, {self.session['name']} 👋",
                 font=FONTS["label"], bg=COLORS["bg"],
                 fg=COLORS["text_muted"]).pack(side="right")

        try:
            summary = db.get_dashboard_summary()
        except Exception as e:
            tk.Label(frame, text=f"Could not load data: {e}",
                     bg=COLORS["bg"], fg=COLORS["danger"]).pack()
            return

        cards = [
            ("🏘️", "Total Properties", summary["properties"],    COLORS["accent"],  "properties"),
            ("👥", "Total Users",       summary["users"],          COLORS["success"], "users"),
            ("💰", "Transactions",      summary["transactions"],   "#7C3AED",         "transactions"),
            ("💵", "Total Revenue",     f"₹{summary['revenue']:,.0f}", "#D97706",    "transactions"),
            ("📅", "Pending Appts",     summary["pending_appointments"], COLORS["danger"], "appointments"),
        ]

        cards_row = tk.Frame(frame, bg=COLORS["bg"])
        cards_row.pack(fill="x", pady=(0, 20))
        for icon, label, value, color, nav in cards:
            c = card_frame(cards_row, padx=20, pady=20)
            c.pack(side="left", padx=8, expand=True, fill="x")
            c.bind("<Button-1>", lambda e, k=nav: self._navigate(k))
            c.config(cursor="hand2")
            tk.Label(c, text=icon, font=("Segoe UI", 28),
                     bg=COLORS["card"]).pack()
            tk.Label(c, text=str(value), font=FONTS["card_num"],
                     bg=COLORS["card"], fg=color).pack()
            tk.Label(c, text=label, font=FONTS["small"],
                     bg=COLORS["card"], fg=COLORS["text_muted"]).pack()

        # Quick actions
        tk.Label(frame, text="Quick Actions",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(10, 8))
        qa = tk.Frame(frame, bg=COLORS["bg"])
        qa.pack(fill="x")
        actions = [
            ("➕ Add Property",   "properties", COLORS["accent"]),
            ("➕ Add User",       "users",       COLORS["success"]),
            ("📊 View Analytics", "analytics",   "#7C3AED"),
            ("🧮 EMI Calc",       "emi",         "#D97706"),
        ]
        for txt, nav, color in actions:
            tk.Button(qa, text=txt, command=lambda k=nav: self._navigate(k),
                      bg=color, fg="white", font=FONTS["btn"],
                      relief="flat", padx=18, pady=10,
                      cursor="hand2").pack(side="left", padx=6)

    # ── Module loaders (lazy imports) ─────────────────────────────────────────
    def _load_users(self):
        from ui.user_management import UserManagement
        UserManagement(self.content, self.session)

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

    def _load_analytics(self):
        from ui.analytics import AnalyticsDashboard
        AnalyticsDashboard(self.content)

    def _load_emi(self):
        from ui.emi_calculator import EMICalculator
        EMICalculator(self.content)

    def _load_pdf(self):
        from ui.pdf_generator import PDFGenerator
        PDFGenerator(self.content, self.session)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.on_logout()
