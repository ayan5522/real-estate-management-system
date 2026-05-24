"""
ui/property_management.py - Full CRUD + image upload + advanced filters
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from utils import (COLORS, FONTS, styled_button, card_frame,
                   style_treeview, populate_tree, validate_price)

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

PROPERTY_TYPES   = ["House", "Apartment", "Villa", "Commercial", "Plot"]
PROPERTY_STATUSES = ["Available", "Under Negotiation", "Sold", "Rented"]


class PropertyManagement:
    def __init__(self, parent, session):
        self.parent = parent
        self.session = session
        self.selected_id = None
        self.image_paths = []
        self.preview_images = []   # keep references alive
        self._build_ui()
        self._load_table()

    # ── Main layout ───────────────────────────────────────────────────────────
    def _build_ui(self):
        frame = tk.Frame(self.parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        hdr = tk.Frame(frame, bg=COLORS["bg"])
        hdr.pack(fill="x", pady=(0, 14))
        tk.Label(hdr, text="Property Management",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(side="left")
        styled_button(hdr, "➕ Add Property", self._show_add_window,
                      bg=COLORS["accent"]).pack(side="right")

        # Filter bar
        self._build_filters(frame)

        # Table
        table_card = card_frame(frame, padx=0, pady=0)
        table_card.pack(fill="both", expand=True, pady=(10, 0))
        self._build_table(table_card)

    # ── Filter bar ───────────────────────────────────────────────────────────
    def _build_filters(self, parent):
        fb = card_frame(parent, padx=12, pady=10)
        fb.pack(fill="x")

        tk.Label(fb, text="Filters:", font=FONTS["bold"],
                 bg=COLORS["card"]).pack(side="left", padx=(0, 8))

        self.filter_type     = tk.StringVar(value="All Types")
        self.filter_status   = tk.StringVar(value="All Status")
        self.filter_location = tk.StringVar()
        self.filter_min_price= tk.StringVar()
        self.filter_max_price= tk.StringVar()

        ttk.Combobox(fb, textvariable=self.filter_type,
                     values=["All Types"] + PROPERTY_TYPES,
                     state="readonly", width=14).pack(side="left", padx=4)

        ttk.Combobox(fb, textvariable=self.filter_status,
                     values=["All Status"] + PROPERTY_STATUSES,
                     state="readonly", width=14).pack(side="left", padx=4)

        tk.Label(fb, text="Location:", font=FONTS["small"],
                 bg=COLORS["card"]).pack(side="left", padx=(8, 2))
        ttk.Entry(fb, textvariable=self.filter_location, width=14).pack(side="left", padx=2)

        tk.Label(fb, text="Min ₹:", font=FONTS["small"],
                 bg=COLORS["card"]).pack(side="left", padx=(8, 2))
        ttk.Entry(fb, textvariable=self.filter_min_price, width=10).pack(side="left", padx=2)

        tk.Label(fb, text="Max ₹:", font=FONTS["small"],
                 bg=COLORS["card"]).pack(side="left", padx=(4, 2))
        ttk.Entry(fb, textvariable=self.filter_max_price, width=10).pack(side="left", padx=2)

        styled_button(fb, "Apply", self._apply_filters,
                      bg=COLORS["accent"], width=8).pack(side="left", padx=6)
        styled_button(fb, "Reset", self._reset_filters,
                      bg=COLORS["text_muted"], width=8).pack(side="left")

    # ── Table ────────────────────────────────────────────────────────────────
    def _build_table(self, parent):
        cols = ("ID", "Title", "Type", "Location", "Price (₹)", "Size", "Status")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=16)
        widths = [50, 200, 110, 160, 120, 80, 120]
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        style_treeview(self.tree)

        # Status colour tags
        self.tree.tag_configure("Available",         background="#D1FAE5")
        self.tree.tag_configure("Sold",              background="#FEE2E2")
        self.tree.tag_configure("Rented",            background="#FEF3C7")
        self.tree.tag_configure("Under Negotiation", background="#DBEAFE")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        btn_row = tk.Frame(parent, bg=COLORS["card"], pady=8, padx=8)
        btn_row.pack(fill="x")
        styled_button(btn_row, "✏️ Edit",     self._edit_selected,   bg=COLORS["warning"], width=10).pack(side="left", padx=4)
        styled_button(btn_row, "🗑️ Delete",   self._delete_selected, bg=COLORS["danger"],  width=10).pack(side="left", padx=4)
        styled_button(btn_row, "🖼️ Images",   self._view_images,     bg="#7C3AED",         width=10).pack(side="left", padx=4)
        styled_button(btn_row, "💰 Sell/Rent",self._sell_rent,        bg=COLORS["success"], width=12).pack(side="left", padx=4)
        styled_button(btn_row, "🔄 Refresh",  self._load_table,       bg=COLORS["accent"],  width=10).pack(side="right", padx=4)

    # ── Add / Edit window ────────────────────────────────────────────────────
    def _show_add_window(self, edit_data=None):
        win = tk.Toplevel(self.parent)
        win.title("Add Property" if not edit_data else "Edit Property")
        win.geometry("700x680")
        win.configure(bg=COLORS["bg"])
        win.grab_set()

        canvas = tk.Canvas(win, bg=COLORS["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=COLORS["bg"], padx=24, pady=24)
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tk.Label(inner, text="Add Property" if not edit_data else "Edit Property",
                 font=FONTS["title"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 16))

        # Form fields
        vars_ = {}
        fields = [
            ("Title *",       "title",       False),
            ("Location *",    "location",    False),
            ("Price (₹) *",   "price",       False),
            ("Size (sqft)",   "size",        False),
        ]
        for label, key, _ in fields:
            tk.Label(inner, text=label, font=FONTS["bold"],
                     bg=COLORS["bg"]).pack(anchor="w")
            v = tk.StringVar()
            ttk.Entry(inner, textvariable=v, width=50).pack(anchor="w", ipady=5, pady=(2, 10))
            vars_[key] = v

        # Type
        tk.Label(inner, text="Type *", font=FONTS["bold"],
                 bg=COLORS["bg"]).pack(anchor="w")
        type_var = tk.StringVar(value=PROPERTY_TYPES[0])
        ttk.Combobox(inner, textvariable=type_var, values=PROPERTY_TYPES,
                     state="readonly", width=48).pack(anchor="w", ipady=5, pady=(2, 10))

        # Status
        tk.Label(inner, text="Status", font=FONTS["bold"],
                 bg=COLORS["bg"]).pack(anchor="w")
        status_var = tk.StringVar(value="Available")
        ttk.Combobox(inner, textvariable=status_var, values=PROPERTY_STATUSES,
                     state="readonly", width=48).pack(anchor="w", ipady=5, pady=(2, 10))

        # Description
        tk.Label(inner, text="Description", font=FONTS["bold"],
                 bg=COLORS["bg"]).pack(anchor="w")
        desc_text = tk.Text(inner, width=50, height=4, font=FONTS["label"])
        desc_text.pack(anchor="w", pady=(2, 10))

        # Images
        self._form_image_paths = list(self.image_paths) if edit_data else []
        img_frame = tk.Frame(inner, bg=COLORS["bg"])
        img_frame.pack(fill="x", pady=(0, 10))
        tk.Label(img_frame, text="Images (max 8):", font=FONTS["bold"],
                 bg=COLORS["bg"]).pack(side="left")
        self._img_count_label = tk.Label(img_frame,
            text=f"{len(self._form_image_paths)} selected",
            font=FONTS["small"], bg=COLORS["bg"], fg=COLORS["text_muted"])
        self._img_count_label.pack(side="left", padx=8)
        styled_button(img_frame, "📁 Browse Images", self._browse_images,
                      bg=COLORS["accent"], width=16).pack(side="left", padx=4)
        styled_button(img_frame, "Clear", self._clear_images,
                      bg=COLORS["text_muted"], width=8).pack(side="left")

        # Pre-fill if editing
        if edit_data:
            vars_["title"].set(edit_data.get("title", ""))
            vars_["location"].set(edit_data.get("location", ""))
            vars_["price"].set(str(edit_data.get("price", "")))
            vars_["size"].set(edit_data.get("size", "") or "")
            type_var.set(edit_data.get("type", PROPERTY_TYPES[0]))
            status_var.set(edit_data.get("status", "Available"))
            if edit_data.get("description"):
                desc_text.insert("1.0", edit_data["description"])
            if edit_data.get("image_paths"):
                self._form_image_paths = [p.strip() for p in
                                           edit_data["image_paths"].split("|") if p.strip()]
            self._img_count_label.config(text=f"{len(self._form_image_paths)} selected")

        # Save button
        def save():
            title    = vars_["title"].get().strip()
            location = vars_["location"].get().strip()
            price    = vars_["price"].get().strip()
            size     = vars_["size"].get().strip()
            ptype    = type_var.get()
            status   = status_var.get()
            desc     = desc_text.get("1.0", "end").strip()
            imgs     = "|".join(self._form_image_paths)

            if not title or not location or not price:
                messagebox.showwarning("Validation", "Title, Location and Price are required.", parent=win)
                return
            if not validate_price(price):
                messagebox.showwarning("Validation", "Price must be a positive number.", parent=win)
                return
            try:
                if edit_data:
                    db.update_property(edit_data["id"], title, ptype, location,
                                       float(price), size, desc, imgs, status)
                    messagebox.showinfo("Success", "Property updated!", parent=win)
                else:
                    db.add_property(title, ptype, location, float(price),
                                    size, desc, imgs, self.session["id"])
                    messagebox.showinfo("Success", "Property added!", parent=win)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win); return

            win.destroy()
            self._load_table()

        styled_button(inner, "💾 Save Property", save,
                      bg=COLORS["success"], width=20).pack(anchor="w", pady=10)

    def _browse_images(self):
        remaining = 8 - len(self._form_image_paths)
        if remaining <= 0:
            messagebox.showwarning("Limit", "Maximum 8 images allowed."); return
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp")],
        )
        added = list(files)[:remaining]
        self._form_image_paths.extend(added)
        self._img_count_label.config(text=f"{len(self._form_image_paths)} selected")

    def _clear_images(self):
        self._form_image_paths = []
        self._img_count_label.config(text="0 selected")

    # ── Table actions ────────────────────────────────────────────────────────
    def _load_table(self, filters=None):
        try:
            props = db.get_all_properties(filters)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        cols = ("id", "title", "type", "location", "price", "size", "status")
        self.tree.delete(*self.tree.get_children())
        for row in props:
            values = [row.get(c, "") for c in cols]
            tag = row.get("status", "Available").replace(" ", "_")
            self.tree.insert("", "end", values=values, tags=(tag,))

    def _apply_filters(self):
        f = {}
        if self.filter_type.get() != "All Types":
            f["type"] = self.filter_type.get()
        if self.filter_status.get() != "All Status":
            f["status"] = self.filter_status.get()
        loc = self.filter_location.get().strip()
        if loc: f["location"] = loc
        mn = self.filter_min_price.get().strip()
        mx = self.filter_max_price.get().strip()
        if mn and validate_price(mn): f["min_price"] = float(mn)
        if mx and validate_price(mx): f["max_price"] = float(mx)
        self._load_table(f)

    def _reset_filters(self):
        self.filter_type.set("All Types")
        self.filter_status.set("All Status")
        self.filter_location.set("")
        self.filter_min_price.set("")
        self.filter_max_price.set("")
        self._load_table()

    def _on_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.selected_id = self.tree.item(sel[0], "values")[0]

    def _edit_selected(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select a property first."); return
        try:
            prop = db.get_property_by_id(self.selected_id)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        if prop:
            self._show_add_window(edit_data=prop)

    def _delete_selected(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select a property first."); return
        if messagebox.askyesno("Confirm", "Delete this property permanently?"):
            try:
                db.delete_property(self.selected_id)
            except Exception as e:
                messagebox.showerror("Error", str(e)); return
            self.selected_id = None
            self._load_table()

    def _view_images(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select a property first."); return
        try:
            prop = db.get_property_by_id(self.selected_id)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        paths = [p.strip() for p in (prop.get("image_paths") or "").split("|") if p.strip()]
        if not paths:
            messagebox.showinfo("No Images", "No images for this property."); return

        win = tk.Toplevel(self.parent)
        win.title(f"Images – {prop['title']}")
        win.geometry("800x500")
        win.configure(bg=COLORS["bg"])
        win.grab_set()

        tk.Label(win, text=f"Images for: {prop['title']}",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(pady=10)

        grid = tk.Frame(win, bg=COLORS["bg"])
        grid.pack(fill="both", expand=True, padx=20)

        self.preview_images.clear()
        if PIL_AVAILABLE:
            for i, path in enumerate(paths[:8]):
                if not os.path.isfile(path): continue
                try:
                    img = Image.open(path).resize((160, 120), Image.LANCZOS)
                    ph = ImageTk.PhotoImage(img)
                    self.preview_images.append(ph)
                    r, c = divmod(i, 4)
                    lbl = tk.Label(grid, image=ph, bg=COLORS["bg"],
                                   relief="ridge", bd=1)
                    lbl.grid(row=r*2, column=c, padx=6, pady=4)
                    tk.Label(grid, text=os.path.basename(path),
                             font=FONTS["small"], bg=COLORS["bg"],
                             fg=COLORS["text_muted"],
                             wraplength=155).grid(row=r*2+1, column=c)
                except Exception:
                    pass
        else:
            for path in paths:
                tk.Label(win, text=path, font=FONTS["small"],
                         bg=COLORS["bg"], fg=COLORS["text_muted"]).pack(anchor="w", padx=20)
            tk.Label(win, text="Install Pillow for image previews.",
                     font=FONTS["small"], bg=COLORS["bg"],
                     fg=COLORS["warning"]).pack()

    def _sell_rent(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select a property first."); return
        try:
            prop = db.get_property_by_id(self.selected_id)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return
        if prop and prop["status"] in ("Sold", "Rented"):
            messagebox.showinfo("Info", "This property is already sold/rented."); return

        win = tk.Toplevel(self.parent)
        win.title("Sell / Rent Property")
        win.geometry("420x360")
        win.configure(bg=COLORS["bg"])
        win.grab_set()

        inner = tk.Frame(win, bg=COLORS["bg"], padx=24, pady=24)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text="Transaction Details",
                 font=FONTS["heading"], bg=COLORS["bg"],
                 fg=COLORS["text"]).pack(anchor="w", pady=(0, 16))

        tk.Label(inner, text=f"Property: {prop['title']}",
                 font=FONTS["bold"], bg=COLORS["bg"],
                 fg=COLORS["text_muted"]).pack(anchor="w", pady=(0, 12))

        v_client  = tk.StringVar()
        v_amount  = tk.StringVar(value=str(prop["price"]))
        v_date    = tk.StringVar(value=__import__("datetime").date.today().isoformat())
        v_type    = tk.StringVar(value="Sale")
        v_notes   = tk.StringVar()

        for label, var, show in [
            ("Client Name *", v_client, ""),
            ("Amount (₹) *",  v_amount, ""),
            ("Date *",        v_date,   ""),
            ("Notes",         v_notes,  ""),
        ]:
            tk.Label(inner, text=label, font=FONTS["bold"],
                     bg=COLORS["bg"]).pack(anchor="w")
            ttk.Entry(inner, textvariable=var, width=38).pack(anchor="w",
                       ipady=5, pady=(2, 8))

        tk.Label(inner, text="Type *", font=FONTS["bold"],
                 bg=COLORS["bg"]).pack(anchor="w")
        ttk.Combobox(inner, textvariable=v_type,
                     values=["Sale", "Rent"], state="readonly",
                     width=36).pack(anchor="w", ipady=5, pady=(2, 10))

        def confirm():
            client = v_client.get().strip()
            amount = v_amount.get().strip()
            date   = v_date.get().strip()
            ttype  = v_type.get()
            notes  = v_notes.get().strip()
            if not client or not amount or not date:
                messagebox.showwarning("Validation", "Client, Amount, Date are required.", parent=win); return
            if not validate_price(amount):
                messagebox.showwarning("Validation", "Enter a valid amount.", parent=win); return
            try:
                db.add_transaction(prop["id"], client, float(amount), ttype, date, notes)
                messagebox.showinfo("Success", f"Property {ttype} recorded!", parent=win)
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=win); return
            win.destroy()
            self._load_table()

        styled_button(inner, "✅ Confirm", confirm,
                      bg=COLORS["success"], width=16).pack(anchor="w", pady=6)
