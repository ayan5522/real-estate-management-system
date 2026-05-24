"""
ui/analytics.py - Analytics dashboard with matplotlib charts
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import COLORS, FONTS, styled_button, card_frame

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL = True
except ImportError:
    MPL = False


class AnalyticsDashboard:
    def __init__(self, parent):
        self.parent = parent
        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self.parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        hdr = tk.Frame(frame, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 16))
        tk.Label(hdr, text="Analytics Dashboard",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")
        styled_button(hdr, "🔄 Refresh", self._refresh,
                      bg=COLORS["accent"]).pack(side="right")

        if not MPL:
            tk.Label(frame,
                     text="⚠️  matplotlib not installed.\nRun: pip install matplotlib",
                     font=FONTS["heading"], bg=COLORS["bg"],
                     fg=COLORS["warning"]).pack(expand=True)
            return

        # Summary stats row
        self.stats_frame = tk.Frame(frame, bg=COLORS["bg"])
        self.stats_frame.pack(fill="x", pady=(0, 16))

        # Charts grid
        charts_frame = tk.Frame(frame, bg=COLORS["bg"])
        charts_frame.pack(fill="both", expand=True)

        self.charts_frame = charts_frame
        self._draw_charts()

    def _refresh(self):
        for w in self.charts_frame.winfo_children():
            w.destroy()
        for w in self.stats_frame.winfo_children():
            w.destroy()
        self._draw_charts()

    def _draw_charts(self):
        try:
            prop_stats  = db.get_property_stats()
            monthly_rev = db.get_monthly_revenue()
            top_locs    = db.get_top_locations()
            summary     = db.get_dashboard_summary()
        except Exception as e:
            tk.Label(self.charts_frame, text=f"Error loading data: {e}",
                     bg=COLORS["bg"], fg=COLORS["danger"]).pack()
            return

        # ── Summary cards ─────────────────────────────────────────────────────
        for icon, label, value, color in [
            ("🏘️", "Properties",   summary["properties"],              COLORS["accent"]),
            ("💰", "Transactions", summary["transactions"],            "#7C3AED"),
            ("💵", "Revenue",      f"₹{summary['revenue']:,.0f}",     COLORS["success"]),
            ("📅", "Pending Appts",summary["pending_appointments"],    COLORS["danger"]),
        ]:
            c = card_frame(self.stats_frame, padx=16, pady=12)
            c.pack(side="left", padx=6, expand=True, fill="x")
            tk.Label(c, text=f"{icon}  {label}", font=FONTS["bold"],
                     bg=COLORS["card"], fg=COLORS["text_muted"]).pack(anchor="w")
            tk.Label(c, text=str(value), font=("Segoe UI", 20, "bold"),
                     bg=COLORS["card"], fg=color).pack(anchor="w")

        # ── 2×2 chart grid ────────────────────────────────────────────────────
        row1 = tk.Frame(self.charts_frame, bg=COLORS["bg"])
        row1.pack(fill="both", expand=True)
        row2 = tk.Frame(self.charts_frame, bg=COLORS["bg"])
        row2.pack(fill="both", expand=True)

        palette = ["#2563EB", "#16A34A", "#DC2626", "#D97706",
                   "#7C3AED", "#0891B2", "#BE185D", "#4D7C0F"]

        # Chart 1 – Pie: property status distribution
        if prop_stats:
            labels = [r["status"] for r in prop_stats]
            values = [r["count"]  for r in prop_stats]
            self._pie_chart(row1, labels, values,
                            "Property Status Distribution", palette)
        else:
            self._empty_chart(row1, "No property data")

        # Chart 2 – Bar: monthly revenue
        if monthly_rev:
            months = [r["month"] for r in monthly_rev][-6:]
            revs   = [float(r["revenue"]) for r in monthly_rev][-6:]
            self._bar_chart(row1, months, revs,
                            "Monthly Revenue (₹)", COLORS["accent"])
        else:
            self._empty_chart(row1, "No revenue data")

        # Chart 3 – Horizontal bar: top locations
        if top_locs:
            locs   = [r["location"][:20] for r in top_locs[:8]]
            counts = [r["count"]         for r in top_locs[:8]]
            self._hbar_chart(row2, locs, counts,
                             "Top Locations", COLORS["success"])
        else:
            self._empty_chart(row2, "No location data")

        # Chart 4 – Donut: sold vs available
        if prop_stats:
            labels = [r["status"] for r in prop_stats]
            values = [r["count"]  for r in prop_stats]
            self._donut_chart(row2, labels, values,
                              "Property Mix", palette)
        else:
            self._empty_chart(row2, "No data")

    # ── Chart helpers ────────────────────────────────────────────────────────
    def _make_fig(self, parent, w=4.5, h=3.2):
        fig = Figure(figsize=(w, h), dpi=88, facecolor="white")
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(side="left", fill="both",
                                     expand=True, padx=8, pady=8)
        return fig

    def _pie_chart(self, parent, labels, values, title, colors):
        fig = self._make_fig(parent)
        ax  = fig.add_subplot(111)
        ax.pie(values, labels=labels, autopct="%1.1f%%",
               colors=colors[:len(values)], startangle=140,
               wedgeprops={"edgecolor": "white", "linewidth": 1.5})
        ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
        fig.tight_layout()

    def _donut_chart(self, parent, labels, values, title, colors):
        fig = self._make_fig(parent)
        ax  = fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct="%1.0f%%",
            colors=colors[:len(values)], startangle=140,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5, "width": 0.5})
        ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
        fig.tight_layout()

    def _bar_chart(self, parent, labels, values, title, color):
        fig = self._make_fig(parent)
        ax  = fig.add_subplot(111)
        bars = ax.bar(labels, values, color=color, edgecolor="white", linewidth=0.8)
        ax.set_title(title, fontsize=10, fontweight="bold")
        ax.tick_params(axis="x", rotation=30, labelsize=7)
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f"₹{x/1e5:.1f}L")
            if max(values, default=0) > 100000 else
            matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
        )
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h,
                    f"{h:,.0f}", ha="center", va="bottom", fontsize=7)
        fig.tight_layout()

    def _hbar_chart(self, parent, labels, values, title, color):
        fig = self._make_fig(parent)
        ax  = fig.add_subplot(111)
        y   = range(len(labels))
        ax.barh(y, values, color=color, edgecolor="white", linewidth=0.8)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_title(title, fontsize=10, fontweight="bold")
        for i, v in enumerate(values):
            ax.text(v + 0.1, i, str(v), va="center", fontsize=7)
        fig.tight_layout()

    def _empty_chart(self, parent, msg):
        c = card_frame(parent, padx=20, pady=40)
        c.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        tk.Label(c, text=msg, font=FONTS["label"],
                 bg=COLORS["card"], fg=COLORS["text_muted"]).pack(expand=True)
