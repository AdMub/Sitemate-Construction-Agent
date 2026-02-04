import sqlite3
import pandas as pd
import json
from datetime import datetime

DB_FILE = "sitemate_projects.db"

def init_db():
    """Initializes the database with Projects, Suppliers, Bids, Expenses, Inventory, and Logs tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Projects Table
    c.execute('''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, location TEXT, soil TEXT, boq_json TEXT, timestamp TEXT)''')
    
    # 2. Suppliers Table
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT, location TEXT, phone TEXT, email TEXT, materials TEXT, rating REAL DEFAULT 5.0, timestamp TEXT)''')

    # 3. Bids Table
    c.execute('''CREATE TABLE IF NOT EXISTS bids (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT, supplier_name TEXT, amount REAL, phone TEXT, status TEXT DEFAULT 'Pending', timestamp TEXT)''')
    
    # 4. Expenses Table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT, item_name TEXT, amount REAL, category TEXT, date TEXT, note TEXT)''')

    # 5. Inventory Table (Current Snapshot)
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            item_name TEXT,
            quantity REAL,
            unit TEXT,
            last_updated TEXT
        )
    ''')

    # 6. Inventory Logs Table (History Ledger)
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            item_name TEXT,
            change_qty REAL,
            unit TEXT,
            operation TEXT,
            date TEXT,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# ==========================================
# 🏗️ PROJECT FUNCTIONS
# ==========================================

def save_project(name, location, soil, boq_df):
    if boq_df is None or boq_df.empty: return False, "Cannot save empty project."
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT OR REPLACE INTO projects (name, location, soil, boq_json, timestamp) VALUES (?, ?, ?, ?, ?)', 
                  (name, location, soil, boq_df.to_json(), datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        return True, "Project saved successfully!"
    except Exception as e: return False, f"Error: {e}"
    finally: conn.close()

def get_all_projects():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, timestamp FROM projects ORDER BY timestamp DESC")
    return c.fetchall()

def load_project_data(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT location, soil, boq_json FROM projects WHERE name=?", (name,))
    row = c.fetchone()
    conn.close()
    if row:
        try: return row[0], row[1], pd.read_json(row[2])
        except: return None, None, None
    return None, None, None

def delete_project(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE name=?", (name,))
    conn.commit()
    conn.close()

# ==========================================
# 👷 SUPPLIER FUNCTIONS
# ==========================================

def register_supplier(name, location, phone, email, materials_list):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO suppliers (company_name, location, phone, email, materials, timestamp) VALUES (?, ?, ?, ?, ?, ?)', 
                  (name, location, phone, email, json.dumps(materials_list), datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def get_db_suppliers(location):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM suppliers WHERE location LIKE ?", (f"%{location}%",))
    rows = c.fetchall()
    conn.close()
    return [{"name": r["company_name"], "markup": 0.98, "rating": "⭐"*int(r["rating"]), "phone": r["phone"], "email": r["email"]} for r in rows]

def get_all_supplier_names():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT company_name FROM suppliers")
    return [r[0] for r in c.fetchall()]

# ==========================================
# 💰 BIDDING ENGINE
# ==========================================

def get_open_tenders(location):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, timestamp, boq_json FROM projects WHERE location LIKE ? ORDER BY timestamp DESC", (f"%{location}%",))
    rows = c.fetchall()
    conn.close()
    tenders = []
    for r in rows:
        try:
            df = pd.read_json(r[2])
            tenders.append({"name": r[0], "date": r[1], "est_value": df['Total Cost'].sum(), "items": len(df)})
        except: pass
    return tenders

def submit_bid(project_name, supplier_name, amount, phone):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO bids (project_name, supplier_name, amount, phone, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (project_name, supplier_name, amount, phone, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def get_bids_for_project(project_name):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM bids WHERE project_name = ? ORDER BY amount ASC", (project_name,))
    return c.fetchall()

# ==========================================
# 🚧 SITE EXECUTION (EXPENSES)
# ==========================================

def log_expense(project, item, amount, category, note):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO expenses (project_name, item_name, amount, category, date, note) VALUES (?, ?, ?, ?, ?, ?)",
                  (project, item, amount, category, datetime.now().strftime("%Y-%m-%d"), note))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def get_project_expenses(project_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM expenses WHERE project_name = ?", (project_name,))
    cols = ["id", "project", "item", "amount", "category", "date", "note"]
    return pd.DataFrame(c.fetchall(), columns=cols)

# ==========================================
# 📦 INVENTORY LEDGER (UPDATED LOGIC)
# ==========================================

def update_inventory(project, item, quantity, unit, operation):
    """
    Updates current stock AND logs the transaction history.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now_date = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M")
    
    try:
        # 1. Update Current Balance (Snapshot)
        c.execute("SELECT quantity FROM inventory WHERE project_name = ? AND item_name = ?", (project, item))
        row = c.fetchone()
        
        current_qty = row[0] if row else 0.0
        
        if operation == 'add':
            new_qty = current_qty + quantity
            log_qty = quantity # Positive for log
            op_label = "Stock IN"
        elif operation == 'remove':
            new_qty = current_qty - quantity
            if new_qty < 0: return False, "Insufficient Stock!"
            log_qty = -quantity # Negative for log
            op_label = "Stock OUT"
        
        if row:
            c.execute("UPDATE inventory SET quantity = ?, last_updated = ? WHERE project_name = ? AND item_name = ?", 
                      (new_qty, now_date, project, item))
        else:
            if operation == 'remove': return False, "Item not in inventory!"
            c.execute("INSERT INTO inventory (project_name, item_name, quantity, unit, last_updated) VALUES (?, ?, ?, ?, ?)",
                      (project, item, quantity, unit, now_date))
        
        # 2. Record Transaction History (Ledger)
        c.execute('''
            INSERT INTO inventory_logs (project_name, item_name, change_qty, unit, operation, date, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (project, item, log_qty, unit, op_label, now_date, now_time))
        
        conn.commit()
        return True, f"Stock updated. New Balance: {new_qty} {unit}"
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_project_inventory(project_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT item_name, quantity, unit, last_updated FROM inventory WHERE project_name = ?", (project_name,))
    cols = ["Item", "Quantity", "Unit", "Last Updated"]
    return pd.DataFrame(c.fetchall(), columns=cols)

def get_inventory_logs(project_name):
    """Fetches the transaction history for the report."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT date, timestamp, item_name, operation, change_qty, unit FROM inventory_logs WHERE project_name = ? ORDER BY date DESC, timestamp DESC", (project_name,))
    cols = ["Date", "Time", "Item", "Action", "Change", "Unit"]
    return pd.DataFrame(c.fetchall(), columns=cols)