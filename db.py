"""
db.py - Database connection and reusable query functions
Real Estate Management System
"""

import mysql.connector
from mysql.connector import Error
import bcrypt

# ─── DB CONFIG ────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Ayan0842@",
    "database": "real_estate_db"
}

# ─── CONNECTION ───────────────────────────────────────────────────────────────
def get_connection():
    """Return a new MySQL connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"Database connection failed: {e}")


def execute_query(query, params=None, fetch=False, fetch_one=False):
    """
    Generic query executor.
    fetch=True  → returns list of dicts
    fetch_one=True → returns single dict
    Otherwise   → commits and returns lastrowid
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            return result
        elif fetch_one:
            result = cursor.fetchone()
            return result
        else:
            conn.commit()
            return cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise RuntimeError(f"Query failed: {e}")
    finally:
        cursor.close()
        conn.close()


# ─── DATABASE INITIALISER ─────────────────────────────────────────────────────
def initialize_database():
    """Create database and all tables if they don't exist."""
    # Connect without specifying a database first
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS real_estate_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE real_estate_db")

        # ── users ──────────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id       INT AUTO_INCREMENT PRIMARY KEY,
                name     VARCHAR(100) NOT NULL,
                username VARCHAR(50)  UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                email    VARCHAR(100),
                contact  VARCHAR(20),
                role     ENUM('admin','agent') DEFAULT 'agent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── properties ─────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                title       VARCHAR(200) NOT NULL,
                type        ENUM('House','Apartment','Villa','Commercial','Plot') NOT NULL,
                location    VARCHAR(200) NOT NULL,
                price       DECIMAL(15,2) NOT NULL,
                size        VARCHAR(50),
                description TEXT,
                image_paths TEXT,
                status      ENUM('Available','Under Negotiation','Sold','Rented') DEFAULT 'Available',
                added_by    INT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)

        # ── transactions ───────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                property_id INT,
                client_name VARCHAR(100) NOT NULL,
                amount      DECIMAL(15,2) NOT NULL,
                type        ENUM('Sale','Rent') NOT NULL,
                date        DATE NOT NULL,
                notes       TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE SET NULL
            )
        """)

        # ── customers ──────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                name       VARCHAR(100) NOT NULL,
                contact    VARCHAR(20),
                email      VARCHAR(100),
                address    TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── appointments ───────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                property_id INT,
                client_name VARCHAR(100) NOT NULL,
                date        DATE NOT NULL,
                time        TIME NOT NULL,
                status      ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
                notes       TEXT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE SET NULL
            )
        """)

        # ── favorites ──────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                user_id     INT,
                property_id INT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE CASCADE,
                FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
                UNIQUE KEY uq_fav (user_id, property_id)
            )
        """)

        conn.commit()

        # ── Seed default admin if none exists ─────────────────────────────────
        cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE role='admin'")
        row = cursor.fetchone()
        if row[0] == 0:
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            cursor.execute("""
                INSERT INTO users (name, username, password, email, contact, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, ("Administrator", "admin", hashed, "admin@realestate.com", "0000000000", "admin"))
            conn.commit()
            print("✅ Default admin created  →  username: admin  |  password: admin123")

        print("✅ Database initialized successfully.")
        cursor.close()
        conn.close()

    except Error as e:
        raise RuntimeError(f"Database initialization failed: {e}")


# ─── AUTH HELPERS ─────────────────────────────────────────────────────────────
def verify_login(username, password):
    """Return user dict if credentials valid, else None."""
    user = execute_query(
        "SELECT * FROM users WHERE username = %s", (username,), fetch_one=True
    )
    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        return user
    return None


def hash_password(plain):
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


# ─── USER CRUD ────────────────────────────────────────────────────────────────
def get_all_users():
    return execute_query("SELECT id,name,username,email,contact,role,created_at FROM users", fetch=True)

def get_user_by_id(uid):
    return execute_query("SELECT * FROM users WHERE id=%s", (uid,), fetch_one=True)

def add_user(name, username, password, email, contact, role):
    hashed = hash_password(password)
    return execute_query(
        "INSERT INTO users (name,username,password,email,contact,role) VALUES (%s,%s,%s,%s,%s,%s)",
        (name, username, hashed, email, contact, role)
    )

def update_user(uid, name, email, contact, role, password=None):
    if password:
        hashed = hash_password(password)
        execute_query(
            "UPDATE users SET name=%s,email=%s,contact=%s,role=%s,password=%s WHERE id=%s",
            (name, email, contact, role, hashed, uid)
        )
    else:
        execute_query(
            "UPDATE users SET name=%s,email=%s,contact=%s,role=%s WHERE id=%s",
            (name, email, contact, role, uid)
        )

def delete_user(uid):
    execute_query("DELETE FROM users WHERE id=%s", (uid,))

def search_users(term):
    t = f"%{term}%"
    return execute_query(
        "SELECT id,name,username,email,contact,role FROM users WHERE name LIKE %s OR username LIKE %s OR email LIKE %s",
        (t, t, t), fetch=True
    )


# ─── PROPERTY CRUD ───────────────────────────────────────────────────────────
def get_all_properties(filters=None):
    query = "SELECT * FROM properties WHERE 1=1"
    params = []
    if filters:
        if filters.get("type"):
            query += " AND type=%s"; params.append(filters["type"])
        if filters.get("location"):
            query += " AND location LIKE %s"; params.append(f"%{filters['location']}%")
        if filters.get("status"):
            query += " AND status=%s"; params.append(filters["status"])
        if filters.get("min_price") is not None:
            query += " AND price>=%s"; params.append(filters["min_price"])
        if filters.get("max_price") is not None:
            query += " AND price<=%s"; params.append(filters["max_price"])
    query += " ORDER BY created_at DESC"
    return execute_query(query, params, fetch=True)

def get_property_by_id(pid):
    return execute_query("SELECT * FROM properties WHERE id=%s", (pid,), fetch_one=True)

def add_property(title, ptype, location, price, size, description, image_paths, added_by):
    return execute_query(
        "INSERT INTO properties (title,type,location,price,size,description,image_paths,added_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
        (title, ptype, location, price, size, description, image_paths, added_by)
    )

def update_property(pid, title, ptype, location, price, size, description, image_paths, status):
    execute_query(
        "UPDATE properties SET title=%s,type=%s,location=%s,price=%s,size=%s,description=%s,image_paths=%s,status=%s WHERE id=%s",
        (title, ptype, location, price, size, description, image_paths, status, pid)
    )

def delete_property(pid):
    execute_query("DELETE FROM properties WHERE id=%s", (pid,))

def update_property_status(pid, status):
    execute_query("UPDATE properties SET status=%s WHERE id=%s", (status, pid))


# ─── TRANSACTION CRUD ─────────────────────────────────────────────────────────
def get_all_transactions():
    return execute_query("""
        SELECT t.*, p.title AS property_title
        FROM transactions t
        LEFT JOIN properties p ON t.property_id=p.id
        ORDER BY t.date DESC
    """, fetch=True)

def add_transaction(property_id, client_name, amount, ttype, date, notes=""):
    tid = execute_query(
        "INSERT INTO transactions (property_id,client_name,amount,type,date,notes) VALUES (%s,%s,%s,%s,%s,%s)",
        (property_id, client_name, amount, ttype, date, notes)
    )
    # Update property status
    new_status = "Sold" if ttype == "Sale" else "Rented"
    update_property_status(property_id, new_status)
    return tid

def search_transactions(term):
    t = f"%{term}%"
    return execute_query("""
        SELECT t.*, p.title AS property_title
        FROM transactions t LEFT JOIN properties p ON t.property_id=p.id
        WHERE t.client_name LIKE %s OR p.title LIKE %s OR t.type LIKE %s
        ORDER BY t.date DESC
    """, (t, t, t), fetch=True)


# ─── CUSTOMER CRUD ────────────────────────────────────────────────────────────
def get_all_customers():
    return execute_query("SELECT * FROM customers ORDER BY created_at DESC", fetch=True)

def add_customer(name, contact, email, address):
    return execute_query(
        "INSERT INTO customers (name,contact,email,address) VALUES (%s,%s,%s,%s)",
        (name, contact, email, address)
    )

def update_customer(cid, name, contact, email, address):
    execute_query(
        "UPDATE customers SET name=%s,contact=%s,email=%s,address=%s WHERE id=%s",
        (name, contact, email, address, cid)
    )

def delete_customer(cid):
    execute_query("DELETE FROM customers WHERE id=%s", (cid,))

def search_customers(term):
    t = f"%{term}%"
    return execute_query(
        "SELECT * FROM customers WHERE name LIKE %s OR email LIKE %s OR contact LIKE %s",
        (t, t, t), fetch=True
    )


# ─── APPOINTMENT CRUD ─────────────────────────────────────────────────────────
def get_all_appointments():
    return execute_query("""
        SELECT a.*, p.title AS property_title
        FROM appointments a LEFT JOIN properties p ON a.property_id=p.id
        ORDER BY a.date DESC, a.time DESC
    """, fetch=True)

def add_appointment(property_id, client_name, date, time, notes=""):
    return execute_query(
        "INSERT INTO appointments (property_id,client_name,date,time,notes) VALUES (%s,%s,%s,%s,%s)",
        (property_id, client_name, date, time, notes)
    )

def update_appointment_status(aid, status):
    execute_query("UPDATE appointments SET status=%s WHERE id=%s", (status, aid))

def delete_appointment(aid):
    execute_query("DELETE FROM appointments WHERE id=%s", (aid,))


# ─── ANALYTICS QUERIES ────────────────────────────────────────────────────────
def get_property_stats():
    return execute_query("""
        SELECT status, COUNT(*) AS count FROM properties GROUP BY status
    """, fetch=True)

def get_monthly_revenue():
    return execute_query("""
        SELECT DATE_FORMAT(date,'%Y-%m') AS month, SUM(amount) AS revenue
        FROM transactions GROUP BY month ORDER BY month DESC LIMIT 12
    """, fetch=True)

def get_top_locations():
    return execute_query("""
        SELECT location, COUNT(*) AS count FROM properties GROUP BY location ORDER BY count DESC LIMIT 10
    """, fetch=True)

def get_dashboard_summary():
    total_props  = execute_query("SELECT COUNT(*) AS c FROM properties",         fetch_one=True)["c"]
    total_users  = execute_query("SELECT COUNT(*) AS c FROM users",              fetch_one=True)["c"]
    total_tx     = execute_query("SELECT COUNT(*) AS c FROM transactions",       fetch_one=True)["c"]
    total_rev    = execute_query("SELECT COALESCE(SUM(amount),0) AS c FROM transactions", fetch_one=True)["c"]
    pending_appt = execute_query("SELECT COUNT(*) AS c FROM appointments WHERE status='Pending'", fetch_one=True)["c"]
    return {
        "properties": total_props,
        "users":      total_users,
        "transactions": total_tx,
        "revenue":    float(total_rev),
        "pending_appointments": pending_appt
    }


# ─── FAVORITES ────────────────────────────────────────────────────────────────
def toggle_favorite(user_id, property_id):
    existing = execute_query(
        "SELECT id FROM favorites WHERE user_id=%s AND property_id=%s",
        (user_id, property_id), fetch_one=True
    )
    if existing:
        execute_query("DELETE FROM favorites WHERE user_id=%s AND property_id=%s", (user_id, property_id))
        return False  # removed
    else:
        execute_query("INSERT INTO favorites (user_id,property_id) VALUES (%s,%s)", (user_id, property_id))
        return True   # added

def get_favorites(user_id):
    return execute_query("""
        SELECT p.* FROM favorites f
        JOIN properties p ON f.property_id=p.id
        WHERE f.user_id=%s
    """, (user_id,), fetch=True)
