"""
ui/appointments.py - Schedule and manage property visit appointments
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import (COLORS, FONTS, styled_button, card_frame,
                   style_treeview, populate_tree)

STATUSES = ["Pending", "Approved", "Rejected"]


class AppointmentsModule:
    def __init__(self, parent, session):
        self.parent  = parent
        self.session = session
        self.selected_id = None
        self._build_ui()
        self._load_table()

    def _build_ui(self):
        frame = tk.Frame(self.parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        hdr = tk.Frame(frame, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 14))
        tk.Label(hdr, text="Appointments",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")
        styled_button(hdr, "➕ Schedule Appointment",
                      self._show_add_window, bg=COLORS["accent"]).pack(side="right")

        cols_layout = tk.Frame(frame, bg=COLORS["bg"])
        cols_layout.pack(fill="both", expand=True)

        tcard = card_frame(cols_layout, padx=0, pady=0)
        tcard.pack(fill="both", expand=True)
        self._build_table(tcard)

    def _build_table(self, parent):
        cols = ("ID", "Property", "Client", "Date", "Time", "Status", "Notes")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=18)
        widths = [50, 200, 140, 100, 80, 110, 200]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        style_treeview(self.tree)
        self.tree.tag_configure("Pending",  background="#FEF3C7", foreground="#92400E")
        self.tree.tag_configure("Approved", background="#D1FAE5", foreground="#065F46")
        self.tree.tag_configure("Rejected", background="#FEE2E2", foreground="#991B1B")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        btn_row = tk.Frame(parent, bg=COLORS["card"], pady=8, padx=8)
        btn_row.pack(fill="x")
        styled_button(btn_row, "✅ Approve",  lambda: self._change_status("Approved"),
                      bg=COLORS["success"], width=10).pack(side="left", padx=4)
        styled_button(btn_row, "❌ Reject",   lambda: self._change_status("Rejected"),
                      bg=COLORS["danger"],  width=10).pack(side="left", padx=4)
        styled_button(btn_row, "🗑️ Delete",  self._delete_selected,
                      bg="#4B5563",         width=10).pack(side="left", padx=4)
        styled_button(btn_row, "🔄 Refresh", self._load_table,
                      bg=COLORS["accent"],  width=10).pack(side="right", padx=4)

    def _load_table(self):
        try:
            rows = db.get_all_appointments()
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        self.tree.delete(*self.tree.get_children())
        cols = ("id", "property_title", "client_name", "date", "time", "status", "notes")
        for row in rows:
            values = [row.get(c, "") for c in cols]
            status = row.get("status", "Pending")
            self.tree.insert("", "end", values=values, tags=(status,))

    def _on_select(self, _):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0], "values")[0]

    def _change_status(self, status):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select an appointment first."); return
        try:
            db.update_appointment_status(self.selected_id, status)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        self._load_table()

    def _delete_selected(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select an appointment first."); return
        if messagebox.askyesno("Confirm", "Delete this appointment?"):
            try:
                db.delete_appointment(self.selected_id)
            except Exception as e:
                messagebox.showerror("Error", str(e)); return
            self.selected_id = None
            self._load_table()

    def _show_add_window(self):
        win = tk.Toplevel(self.parent)
        win.title("Schedule Appointment")
        win.geometry("480x500")
        win.configure(bg=COLORS["bg"])
        win.grab_set()

        inner = tk.Frame(win, bg=COLORS["bg"], padx=28, pady=28)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="Schedule Appointment",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 18))

        # Property selector
        tk.Label(inner, text="Property *", font=FONTS["bold"],
                 bg=COLORS["bg"]).pack(anchor="w")
        try:
            props = db.get_all_properties({"status": "Available"})
        except Exception:
            props = []
        prop_map = {f"[{p['id']}] {p['title']}": p["id"] for p in props}
        prop_var = tk.StringVar()
        prop_cb = ttk.Combobox(inner, textvariable=prop_var,
                               values=list(prop_map.keys()),
                               state="readonly", width=44)
        prop_cb.pack(anchor="w", ipady=5, pady=(2, 10))

        v_client = tk.StringVar()
        v_date   = tk.StringVar(value=datetime.date.today().isoformat())
        v_time   = tk.StringVar(value="10:00")
        v_notes  = tk.StringVar()

        for label, var in [("Client Name *", v_client),
                            ("Date (YYYY-MM-DD) *", v_date),
                            ("Time (HH:MM) *",      v_time),
                            ("Notes",               v_notes)]:
            tk.Label(inner, text=label, font=FONTS["bold"],
                     bg=COLORS["bg"]).pack(anchor="w")
            ttk.Entry(inner, textvariable=var, width=46).pack(anchor="w",
                       ipady=5, pady=(2, 10))

        def save():
            key = prop_var.get()
            if not key:
                messagebox.showwarning("Validation", "Select a property.", parent=win); return
            client = v_client.get().strip()
            date   = v_date.get().strip()
            time   = v_time.get().strip()
            notes  = v_notes.get().strip()
            if not client or not date or not time:
                messagebox.showwarning("Validation", "Client, Date and Time are required.", parent=win)
                return
            # Basic date/time validation
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
                datetime.datetime.strptime(time, "%H:%M")
            except ValueError:
                messagebox.showwarning("Validation", "Use YYYY-MM-DD and HH:MM format.", parent=win)
                return
            try:
                db.add_appointment(prop_map[key], client, date, time, notes)
                messagebox.showinfo("Success", "Appointment scheduled!", parent=win)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win); return
            win.destroy()
            self._load_table()

        styled_button(inner, "📅 Schedule", save,
                      bg=COLORS["success"], width=18).pack(anchor="w", pady=8)
