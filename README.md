# 🏠 Real Estate Management System

A fully featured desktop application built with **Python + Tkinter + MySQL**.

---

## 📁 Project Structure

```
real_estate/
├── main.py                    # Entry point
├── db.py                      # Database layer (all CRUD + queries)
├── utils.py                   # Shared theme, colours, widget helpers
├── requirements.txt           # pip dependencies
├── setup_database.sql         # Optional: run manually in MySQL
│
└── ui/
    ├── __init__.py
    ├── login.py               # Login screen with bcrypt auth
    ├── admin_dashboard.py     # Admin dashboard + sidebar navigation
    ├── agent_dashboard.py     # Agent dashboard + sidebar navigation
    ├── user_management.py     # Add / View / Edit / Delete users
    ├── profile.py             # User profile page
    ├── property_management.py # Full property CRUD + image upload + filters
    ├── transactions.py        # View & search transactions
    ├── customers.py           # Customer CRUD + purchase history
    ├── appointments.py        # Schedule & manage appointments
    ├── analytics.py           # Matplotlib charts dashboard
    ├── emi_calculator.py      # EMI / loan calculator + amortization
    └── pdf_generator.py       # PDF invoice generator (reportlab)
```

---

## ⚙️ Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| MySQL Server | 8.0+ |
| pip | latest |

---

## 🚀 Quick Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install mysql-connector-python bcrypt Pillow matplotlib reportlab
```

### 2. Configure the database

Open `db.py` and confirm the connection settings match your MySQL installation:

```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "Ayan@0842",   # ← change if needed
    "database": "real_estate_db"
}
```

### 3. Run the application

```bash
python main.py
```

The app automatically:
- Creates the `real_estate_db` database
- Creates all required tables
- Seeds a default **admin** user if none exists

### 4. Login with default credentials

| Field    | Value      |
|----------|-----------|
| Username | `admin`    |
| Password | `admin123` |

> ⚠️ Change the default password after first login via **My Profile**.

---

## 🗄️ Database Tables

| Table          | Purpose |
|----------------|---------|
| `users`        | System users (admin / agent) with bcrypt passwords |
| `properties`   | Property listings with images, status, type |
| `transactions` | Sale / rent records linked to properties |
| `customers`    | Client contact book |
| `appointments` | Property visit scheduling |
| `favorites`    | Bookmarked properties per user |

---

## 🔐 Role Permissions

| Feature                | Admin | Agent |
|------------------------|-------|-------|
| User Management        | ✅    | ❌    |
| Analytics Dashboard    | ✅    | ❌    |
| Property Management    | ✅    | ✅    |
| Transactions           | ✅    | ✅    |
| Customers              | ✅    | ✅    |
| Appointments           | ✅    | ✅    |
| EMI Calculator         | ✅    | ✅    |
| PDF Generator          | ✅    | ✅    |

---

## 📦 Module Overview

### 🔑 Login System (`ui/login.py`)
- Username / password authentication
- bcrypt password hashing
- Show/hide password toggle
- Role-based routing (Admin → Admin Dashboard, Agent → Agent Dashboard)
- Default credentials hint

### 🏠 Admin Dashboard (`ui/admin_dashboard.py`)
- Sidebar navigation with active state highlighting
- Summary cards: total properties, users, transactions, revenue, pending appointments
- Quick action buttons
- Lazy loading of all sub-modules

### 👥 User Management (`ui/user_management.py`)
- Add, Edit, Delete users
- Live search across name / username / email
- Role assignment (admin / agent)
- Cannot delete own account
- Input validation (email format, required fields)

### 🏘️ Property Management (`ui/property_management.py`)
- Add / Edit / Delete properties
- Upload up to 8 images (stored as pipe-separated paths)
- Image preview gallery (requires Pillow)
- Status colour-coding in table (Available=green, Sold=red, Rented=yellow)
- Advanced filters: type, status, location, min/max price
- Sell/Rent property directly from table (creates transaction + updates status)

### 💰 Transactions (`ui/transactions.py`)
- View all sale and rent transactions
- Summary stats: total count, revenue, sales, rentals
- Live search by client name, property, type
- Colour-coded rows (Sale=green, Rent=yellow)

### 👤 Customers (`ui/customers.py`)
- Add / Edit / Delete customers
- Live search
- View full purchase history per customer

### 📅 Appointments (`ui/appointments.py`)
- Schedule property visits
- Status management: Pending → Approved / Rejected
- Colour-coded by status
- Date/time validation

### 📊 Analytics (`ui/analytics.py`)
- Summary stat cards
- Pie chart: property status distribution
- Bar chart: monthly revenue (last 6 months)
- Horizontal bar: top locations by listing count
- Donut chart: property mix
- Requires `matplotlib`

### 🧮 EMI Calculator (`ui/emi_calculator.py`)
- Inputs: property price, down payment, annual interest rate, tenure
- Outputs: monthly EMI, total payment, total interest
- Full amortization schedule table
- Pie chart: principal vs interest split
- Stacked area chart: yearly breakdown
- Requires `matplotlib`

### 📄 PDF Generator (`ui/pdf_generator.py`)
- Select any transaction from a searchable list
- Preview invoice content in-app
- Generate professional PDF invoice with:
  - Invoice header & number
  - Property details
  - Client details
  - Payment summary
  - Footer with generation timestamp
- Requires `reportlab`

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|---------|
| `mysql.connector` not found | `pip install mysql-connector-python` |
| Database connection failed | Check `db.py` credentials; ensure MySQL is running |
| Images not showing | `pip install Pillow` |
| Charts not showing | `pip install matplotlib` |
| PDF not generating | `pip install reportlab` |
| `bcrypt` error | `pip install bcrypt` |

---

## 🔧 Optional: Manual DB Setup

If you prefer to set up the database manually:

```bash
mysql -u root -p < setup_database.sql
```

This creates the database, all tables, and a default admin user.

---

## 📝 Notes

- Image files are referenced by **file path** — moving or deleting the original files will break previews.
- The `favorites` table is implemented in `db.py` and can be wired to a UI with `db.toggle_favorite(user_id, property_id)` and `db.get_favorites(user_id)`.
- All monetary values are stored as `DECIMAL(15,2)` — suitable for amounts up to ₹999,999,999,999.99.
