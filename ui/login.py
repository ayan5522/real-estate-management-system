"""
ui/login.py - Login screen

FIX 1: Window is now resizable — resizable(True, True), proper min size set,
        grid weights applied so panels scale correctly on resize/maximize.

FIX 2: Receives a Toplevel window (not root). On success it passes itself
        back to main.py's callback so main.py can destroy it cleanly before
        opening the dashboard. No login widgets can bleed into the dashboard.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import COLORS, FONTS


class LoginWindow:
    def __init__(self, window, on_success):
        """
        window     : tk.Toplevel (passed from main.py)
        on_success : callback(user_dict, window) — main.py destroys window
                     and opens the dashboard
        """
        self.window     = window
        self.on_success = on_success
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_ui(self):
        win = self.window
        win.title("Real Estate Management System – Login")

        # ── Window sizing & resizing (FIX 1) ──────────────────────────────────
        win.resizable(True, True)           # allow resize in both directions
        win.minsize(820, 520)               # prevent it from going too small

        # Centre on screen
        win.update_idletasks()
        w, h   = 1050, 640
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x      = (sw - w) // 2
        y      = (sh - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")

        win.configure(bg=COLORS["bg"])

        # ── Root grid: 1 row × 2 columns, both expandable ─────────────────────
        win.rowconfigure(0, weight=1)
        win.columnconfigure(0, weight=2)    # left decorative panel
        win.columnconfigure(1, weight=3)    # right login panel

        # ── LEFT decorative panel ─────────────────────────────────────────────
        left = tk.Frame(win, bg=COLORS["sidebar"])
        left.grid(row=0, column=0, sticky="nsew")

        # Left panel scales vertically — centre content with a spacer approach
        left.rowconfigure(0, weight=1)
        left.rowconfigure(99, weight=1)
        left.columnconfigure(0, weight=1)

        content_left = tk.Frame(left, bg=COLORS["sidebar"])
        content_left.grid(row=1, column=0)

        tk.Label(content_left, text="🏠", font=("Segoe UI", 64),
                 bg=COLORS["sidebar"], fg=COLORS["accent"]).pack(pady=(0, 10))
        tk.Label(content_left, text="Real Estate\nManagement System",
                 font=("Segoe UI", 22, "bold"),
                 bg=COLORS["sidebar"], fg="white",
                 justify="center").pack()
        tk.Label(content_left,
                 text="Manage properties, clients,\ntransactions and more.",
                 font=("Segoe UI", 11), bg=COLORS["sidebar"],
                 fg="#94A3B8", justify="center").pack(pady=18)

        stats_frame = tk.Frame(content_left, bg=COLORS["sidebar_btn"],
                                pady=16, padx=20)
        stats_frame.pack(fill="x", padx=20, pady=(10, 0))
        for icon, label in [("🏘️", "Properties"), ("👥", "Users"), ("📊", "Reports")]:
            col = tk.Frame(stats_frame, bg=COLORS["sidebar_btn"])
            col.pack(side="left", expand=True)
            tk.Label(col, text=icon, font=("Segoe UI", 18),
                     bg=COLORS["sidebar_btn"], fg="white").pack()
            tk.Label(col, text=label, font=("Segoe UI", 8),
                     bg=COLORS["sidebar_btn"], fg="#94A3B8").pack()

        # ── RIGHT login panel ─────────────────────────────────────────────────
        right = tk.Frame(win, bg=COLORS["white"])
        right.grid(row=0, column=1, sticky="nsew")

        # Centre the form card inside the right panel
        right.rowconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)
        right.columnconfigure(2, weight=1)

        inner = tk.Frame(right, bg=COLORS["white"])
        inner.grid(row=1, column=1)         # vertically + horizontally centred

        # ── Form content ──────────────────────────────────────────────────────
        tk.Label(inner, text="Welcome Back",
                 font=("Segoe UI", 26, "bold"),
                 bg=COLORS["white"], fg=COLORS["text"]).pack(anchor="w")
        tk.Label(inner, text="Sign in to your account",
                 font=FONTS["label"], bg=COLORS["white"],
                 fg=COLORS["text_muted"]).pack(anchor="w", pady=(2, 28))

        # Username
        tk.Label(inner, text="Username", font=FONTS["bold"],
                 bg=COLORS["white"], fg=COLORS["text"]).pack(anchor="w")
        self.username_var = tk.StringVar()
        uentry = ttk.Entry(inner, textvariable=self.username_var,
                           width=34, font=FONTS["label"])
        uentry.pack(anchor="w", ipady=7, pady=(4, 16))
        uentry.focus()

        # Password
        tk.Label(inner, text="Password", font=FONTS["bold"],
                 bg=COLORS["white"], fg=COLORS["text"]).pack(anchor="w")
        self.password_var = tk.StringVar()
        pframe = tk.Frame(inner, bg=COLORS["white"])
        pframe.pack(anchor="w", pady=(4, 6))
        self.pentry = ttk.Entry(pframe, textvariable=self.password_var,
                                width=31, font=FONTS["label"], show="●")
        self.pentry.pack(side="left", ipady=7)
        self.show_pw = False
        tk.Button(pframe, text="👁", font=("Segoe UI", 13),
                  bg=COLORS["white"], relief="flat", cursor="hand2",
                  command=self._toggle_password).pack(side="left", padx=6)

        # Spacer
        tk.Frame(inner, bg=COLORS["white"], height=18).pack()

        # Login button
        login_btn = tk.Button(inner, text="Sign In  →",
                              command=self._login,
                              bg=COLORS["accent"], fg="white",
                              font=("Segoe UI", 12, "bold"),
                              relief="flat", cursor="hand2",
                              padx=24, pady=12, width=22)
        login_btn.pack(anchor="w")
        login_btn.bind("<Enter>", lambda e: login_btn.config(bg=COLORS["accent_hover"]))
        login_btn.bind("<Leave>", lambda e: login_btn.config(bg=COLORS["accent"]))

        # Hint box
        hint = tk.Frame(inner, bg="#F1F5F9", pady=10, padx=14)
        hint.pack(fill="x", pady=(22, 0))
        tk.Label(hint, text="Default Admin  →  admin / admin123",
                 font=FONTS["small"], bg="#F1F5F9",
                 fg=COLORS["text_muted"]).pack()

        # Bind Enter key to this window only
        win.bind("<Return>", lambda e: self._login())

    # ── Actions ───────────────────────────────────────────────────────────────
    def _toggle_password(self):
        self.show_pw = not self.show_pw
        self.pentry.config(show="" if self.show_pw else "●")

    def _login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Required",
                                   "Please enter both username and password.",
                                   parent=self.window)
            return

        try:
            user = db.verify_login(username, password)
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self.window)
            return

        if user:
            # Pass self.window so main.py can destroy it before opening dashboard
            self.on_success(user, self.window)
        else:
            messagebox.showerror("Login Failed",
                                 "Invalid username or password.",
                                 parent=self.window)
            self.password_var.set("")
