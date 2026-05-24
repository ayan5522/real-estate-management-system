"""
utils.py - Shared theme, colors, fonts, and utility helpers
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re

# ─── COLOUR PALETTE ───────────────────────────────────────────────────────────
COLORS = {
    "bg":           "#F0F4F8",
    "sidebar":      "#1A2332",
    "sidebar_btn":  "#253347",
    "sidebar_hover":"#2E4A6E",
    "accent":       "#2563EB",
    "accent_hover": "#1D4ED8",
    "success":      "#16A34A",
    "danger":       "#DC2626",
    "warning":      "#D97706",
    "white":        "#FFFFFF",
    "card":         "#FFFFFF",
    "text":         "#1E293B",
    "text_muted":   "#64748B",
    "border":       "#E2E8F0",
    "header_bg":    "#1E3A5F",
}

FONTS = {
    "title":   ("Segoe UI", 22, "bold"),
    "heading": ("Segoe UI", 14, "bold"),
    "label":   ("Segoe UI", 10),
    "bold":    ("Segoe UI", 10, "bold"),
    "small":   ("Segoe UI", 9),
    "sidebar": ("Segoe UI", 11),
    "btn":     ("Segoe UI", 10, "bold"),
    "card_num":("Segoe UI", 28, "bold"),
}

# ─── STYLED WIDGET HELPERS ───────────────────────────────────────────────────
def styled_button(parent, text, command, bg=None, fg="white", width=14, **kw):
    bg = bg or COLORS["accent"]
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, font=FONTS["btn"],
        relief="flat", bd=0, cursor="hand2",
        padx=10, pady=6, width=width, **kw
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=_darken(bg)))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg))
    return btn


def styled_entry(parent, textvariable=None, width=28, show=None, **kw):
    e = ttk.Entry(parent, textvariable=textvariable, width=width, show=show or "", **kw)
    return e


def card_frame(parent, **kw):
    return tk.Frame(parent, bg=COLORS["card"], relief="flat",
                    highlightbackground=COLORS["border"], highlightthickness=1, **kw)


def section_label(parent, text, **kw):
    return tk.Label(parent, text=text, bg=COLORS["card"],
                    fg=COLORS["text"], font=FONTS["heading"], **kw)


def _darken(hex_color):
    """Slightly darken a hex colour string."""
    try:
        r = max(0, int(hex_color[1:3], 16) - 20)
        g = max(0, int(hex_color[3:5], 16) - 20)
        b = max(0, int(hex_color[5:7], 16) - 20)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


# ─── TREEVIEW STYLING ────────────────────────────────────────────────────────
def style_treeview(tree: ttk.Treeview):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview",
        background=COLORS["white"],
        foreground=COLORS["text"],
        rowheight=28,
        fieldbackground=COLORS["white"],
        font=FONTS["label"]
    )
    style.configure("Custom.Treeview.Heading",
        background=COLORS["header_bg"],
        foreground="white",
        font=FONTS["bold"],
        relief="flat"
    )
    style.map("Custom.Treeview",
        background=[("selected", COLORS["accent"])],
        foreground=[("selected", "white")]
    )
    tree.configure(style="Custom.Treeview")
    # Alternating row tags
    tree.tag_configure("odd",  background="#F8FAFC")
    tree.tag_configure("even", background=COLORS["white"])


def populate_tree(tree, rows, columns):
    """Clear and fill a Treeview."""
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        tag = "odd" if i % 2 == 0 else "even"
        values = [row.get(c, "") for c in columns]
        tree.insert("", "end", values=values, tags=(tag,))


# ─── VALIDATION ───────────────────────────────────────────────────────────────
def validate_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def validate_phone(phone):
    return re.match(r"^\+?[\d\s\-]{7,15}$", phone) is not None

def validate_price(price_str):
    try:
        v = float(price_str)
        return v > 0
    except (ValueError, TypeError):
        return False


# ─── SCROLLABLE FRAME ────────────────────────────────────────────────────────
class ScrollableFrame(tk.Frame):
    """A vertically scrollable container."""
    def __init__(self, parent, bg=None, **kw):
        super().__init__(parent, bg=bg or COLORS["bg"], **kw)
        canvas = tk.Canvas(self, bg=bg or COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=bg or COLORS["bg"])
        self.inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
