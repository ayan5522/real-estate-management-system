"""
ui/emi_calculator.py - EMI / Loan calculator with amortization schedule
"""

import tkinter as tk
from tkinter import ttk
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import COLORS, FONTS, styled_button, card_frame

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL = True
except ImportError:
    MPL = False


class EMICalculator:
    def __init__(self, parent):
        self.parent = parent
        self._build_ui()

    def _build_ui(self):
        frame = tk.Frame(self.parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="EMI / Loan Calculator",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 20))

        main = tk.Frame(frame, bg=COLORS["bg"])
        main.pack(fill="both", expand=True)

        # ── Input card ────────────────────────────────────────────────────────
        left = card_frame(main, padx=28, pady=28, width=350)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="Loan Details",
                 font=FONTS["heading"], bg=COLORS["card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 16))

        self.vars = {}
        fields = [
            ("Property Price (₹)",      "price",    "5000000"),
            ("Down Payment (₹)",        "down",     "1000000"),
            ("Annual Interest Rate (%)", "rate",     "8.5"),
            ("Loan Tenure (Years)",      "tenure",   "20"),
        ]
        for label, key, default in fields:
            tk.Label(left, text=label, font=FONTS["bold"],
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            v = tk.StringVar(value=default)
            e = ttk.Entry(left, textvariable=v, width=30, font=FONTS["label"])
            e.pack(anchor="w", ipady=6, pady=(2, 12))
            self.vars[key] = v

        styled_button(left, "🧮  Calculate EMI", self._calculate,
                      bg=COLORS["accent"], width=22).pack(anchor="w", pady=(8, 0))

        # Formula note
        tk.Label(left,
                 text="Formula:  EMI = P·r·(1+r)ⁿ / ((1+r)ⁿ−1)\n"
                      "P = Principal  r = Monthly rate  n = Months",
                 font=("Segoe UI", 8), bg=COLORS["card"],
                 fg=COLORS["text_muted"], justify="left").pack(anchor="w", pady=(14, 0))

        # ── Results card ──────────────────────────────────────────────────────
        right = tk.Frame(main, bg=COLORS["bg"])
        right.pack(side="right", fill="both", expand=True, padx=(14, 0))

        self.result_card = card_frame(right, padx=24, pady=20)
        self.result_card.pack(fill="x", pady=(0, 14))
        self._result_placeholder()

        # Amortization table
        self.table_frame = card_frame(right, padx=0, pady=0)
        self.table_frame.pack(fill="both", expand=True)
        self._build_table(self.table_frame)

        # Chart area
        self.chart_frame = card_frame(right, padx=0, pady=0)
        self.chart_frame.pack(fill="x", pady=(14, 0))

    def _result_placeholder(self):
        for w in self.result_card.winfo_children():
            w.destroy()
        tk.Label(self.result_card,
                 text="Enter loan details and click Calculate.",
                 font=FONTS["label"], bg=COLORS["card"],
                 fg=COLORS["text_muted"]).pack()

    def _build_table(self, parent):
        cols = ("Month", "EMI (₹)", "Principal (₹)", "Interest (₹)", "Balance (₹)")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        widths = [60, 110, 120, 110, 120]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        from utils import style_treeview
        style_treeview(self.tree)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _calculate(self):
        try:
            price   = float(self.vars["price"].get().replace(",", ""))
            down    = float(self.vars["down"].get().replace(",", ""))
            rate    = float(self.vars["rate"].get())
            tenure  = int(self.vars["tenure"].get())
        except ValueError:
            tk.messagebox.showwarning("Input Error", "Please enter valid numeric values.")
            return

        principal = price - down
        if principal <= 0:
            tk.messagebox.showwarning("Input Error", "Down payment must be less than property price.")
            return
        if rate <= 0 or tenure <= 0:
            tk.messagebox.showwarning("Input Error", "Rate and tenure must be positive.")
            return

        monthly_rate = rate / (12 * 100)
        n            = tenure * 12
        if monthly_rate == 0:
            emi = principal / n
        else:
            emi = principal * monthly_rate * (1 + monthly_rate)**n / ((1 + monthly_rate)**n - 1)

        total_payment = emi * n
        total_interest = total_payment - principal

        # ── Result summary ────────────────────────────────────────────────────
        for w in self.result_card.winfo_children():
            w.destroy()
        tk.Label(self.result_card, text="Loan Summary",
                 font=FONTS["heading"], bg=COLORS["card"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 10))

        results_row = tk.Frame(self.result_card, bg=COLORS["card"])
        results_row.pack(fill="x")
        for label, value, color in [
            ("Monthly EMI",     f"₹{emi:,.0f}",            COLORS["accent"]),
            ("Total Payment",   f"₹{total_payment:,.0f}",  COLORS["success"]),
            ("Total Interest",  f"₹{total_interest:,.0f}", COLORS["danger"]),
            ("Loan Amount",     f"₹{principal:,.0f}",      "#7C3AED"),
        ]:
            col = tk.Frame(results_row, bg=COLORS["card"])
            col.pack(side="left", expand=True)
            tk.Label(col, text=label, font=FONTS["small"],
                     bg=COLORS["card"], fg=COLORS["text_muted"]).pack()
            tk.Label(col, text=value, font=("Segoe UI", 16, "bold"),
                     bg=COLORS["card"], fg=color).pack()

        # ── Amortization schedule ─────────────────────────────────────────────
        self.tree.delete(*self.tree.get_children())
        balance = principal
        principals, interests = [], []
        for month in range(1, n + 1):
            interest_comp = balance * monthly_rate
            principal_comp = emi - interest_comp
            balance -= principal_comp
            principals.append(principal_comp)
            interests.append(interest_comp)
            tag = "odd" if month % 2 == 0 else "even"
            self.tree.insert("", "end",
                values=(month, f"{emi:,.0f}", f"{principal_comp:,.0f}",
                        f"{interest_comp:,.0f}", f"{max(balance,0):,.0f}"),
                tags=(tag,))

        # ── Pie chart (principal vs interest) ────────────────────────────────
        for w in self.chart_frame.winfo_children():
            w.destroy()
        if MPL:
            fig = Figure(figsize=(5, 2.5), dpi=88, facecolor="white")
            ax  = fig.add_subplot(121)
            ax.pie([principal, total_interest],
                   labels=["Principal", "Interest"],
                   colors=[COLORS["accent"], COLORS["danger"]],
                   autopct="%1.1f%%", startangle=90,
                   wedgeprops={"edgecolor": "white"})
            ax.set_title("Principal vs Interest", fontsize=9)

            ax2 = fig.add_subplot(122)
            years = list(range(1, tenure + 1))
            yr_prin = [sum(principals[(y-1)*12:y*12]) for y in years]
            yr_int  = [sum(interests[ (y-1)*12:y*12]) for y in years]
            ax2.stackplot(years, yr_prin, yr_int,
                          labels=["Principal", "Interest"],
                          colors=[COLORS["accent"], COLORS["danger"]],
                          alpha=0.7)
            ax2.set_title("Yearly Breakdown", fontsize=9)
            ax2.legend(fontsize=7)
            ax2.tick_params(labelsize=7)
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.get_tk_widget().pack(fill="x")
