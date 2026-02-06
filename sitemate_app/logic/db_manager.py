# --- COMPATIBILITY PATCH (Fixes asyncio error on Python 3.10+) ---
import asyncio
if not hasattr(asyncio, 'coroutine'):
    asyncio.coroutine = lambda x: x
# -----------------------------------------------------------------

import sqlite3
import pandas as pd
import json
from datetime import datetime
from io import StringIO
import streamlit as st

# --- ALGOLIA INTEGRATION ---
# Now it is safe to import because we patched asyncio
from algoliasearch.search_client import SearchClient

ALGOLIA_READY = False
try:
    if "ALGOLIA_APP_ID" in st.secrets and "ALGOLIA_API_KEY" in st.secrets:
        client = SearchClient.create(st.secrets["ALGOLIA_APP_ID"], st.secrets["ALGOLIA_API_KEY"])
        index_suppliers = client.init_index("sitemate_suppliers")
        index_projects = client.init_index("sitemate_projects")
        
        # Configure settings for better relevance
        index_suppliers.set_settings({'searchableAttributes': ['company_name', 'materials', 'location']})
        index_projects.set_settings({'searchableAttributes': ['name', 'location', 'materials_needed']})
        
        ALGOLIA_READY = True
        print("✅ Algolia Connected Successfully")
    else:
        print("⚠️ Algolia keys not found in secrets.toml")
except Exception as e:
    print(f"⚠️ Algolia Connection Error: {e}")
    # We do NOT stop the app here. We let it run on SQLite fallback.

# --- SQLITE CONFIG ---
DB_FILE = "sitemate_projects.db"

def init_db():
    """Initializes the database with all 8 tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    tables = [
        '''CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, location TEXT, soil TEXT, boq_json TEXT, timestamp TEXT)''',
        '''CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, company_name TEXT, location TEXT, phone TEXT, email TEXT, materials TEXT, rating REAL DEFAULT 5.0, timestamp TEXT)''',
        '''CREATE TABLE IF NOT EXISTS bids (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT, supplier_name TEXT, amount REAL, phone TEXT, status TEXT DEFAULT 'Pending', timestamp TEXT)''',
        '''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT, item_name TEXT, amount REAL, category TEXT, date TEXT, note TEXT)''',
        '''CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT, item_name TEXT, quantity REAL, unit TEXT, last_updated TEXT)''',
        '''CREATE TABLE IF NOT EXISTS inventory_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT, item_name TEXT, change_qty REAL, unit TEXT, operation TEXT, date TEXT, timestamp TEXT)''',
        '''CREATE TABLE IF NOT EXISTS site_photos (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT, image_path TEXT, caption TEXT, timestamp TEXT)''',
        '''CREATE TABLE IF NOT EXISTS site_diary (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT, date TEXT, weather TEXT, labor_count TEXT, work_done TEXT, issues TEXT, timestamp TEXT)'''
    ]
    
    for query in tables:
        c.execute(query)
    
    conn.commit()
    conn.close()

# Ensure DB is initialized
init_db()

# ==========================================
# 🏗️ PROJECT FUNCTIONS (HYBRID)
# ==========================================

def save_project(name, location, soil, boq_df):
    if boq_df is None or boq_df.empty: return False, "Cannot save empty project."
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # 1. SQLite Write (Source of Truth)
        c.execute('INSERT OR REPLACE INTO projects (name, location, soil, boq_json, timestamp) VALUES (?, ?, ?, ?, ?)', 
                  (name, location, soil, boq_df.to_json(), datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        
        # 2. Algolia Sync (Search Index)
        if ALGOLIA_READY:
            try:
                # Extract key data for searchability
                total_val = float(boq_df['Total Cost'].sum())
                # Safe extraction of materials
                material_list = boq_df['Item'].tolist() if 'Item' in boq_df.columns else []
                
                record = {
                    "objectID": name.replace(" ", "_"), # Unique ID
                    "name": name,
                    "location": location,
                    "soil": soil,
                    "est_value": total_val,
                    "materials_needed": material_list,
                    "timestamp": datetime.now().timestamp(),
                    "date_str": datetime.now().strftime("%Y-%m-%d")
                }
                index_projects.save_object(record)
                print(f"🚀 Pushed Project '{name}' to Algolia!")
            except Exception as alg_err:
                print(f"Algolia Sync Error: {alg_err}")
                st.error(f"⚠️ Algolia Sync Failed: {alg_err}")

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
        try: 
            return row[0], row[1], pd.read_json(StringIO(row[2]))
        except: return None, None, None
    return None, None, None

def delete_project(name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE name=?", (name,))
    conn.commit()
    conn.close()
    
    # Remove from Algolia too
    if ALGOLIA_READY:
        try:
            index_projects.delete_object(name.replace(" ", "_"))
        except: pass

# ==========================================
# 👷 SUPPLIER FUNCTIONS (HYBRID)
# ==========================================

def register_supplier(name, location, phone, email, materials_list):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # 1. Save to SQLite
        c.execute('INSERT INTO suppliers (company_name, location, phone, email, materials, timestamp) VALUES (?, ?, ?, ?, ?, ?)', 
                  (name, location, phone, email, json.dumps(materials_list), datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        
        # 2. Sync to Algolia
        if ALGOLIA_READY:
            try:
                record = {
                    "objectID": email, # Unique ID
                    "company_name": name,
                    "location": location,
                    "phone": phone,
                    "email": email,
                    "materials": materials_list, # Searchable array!
                    "rating": 5.0
                }
                index_suppliers.save_object(record)
                print(f"🚀 Registered Supplier '{name}' on Algolia!")
            except Exception as alg_err:
                print(f"Algolia Sync Error: {alg_err}")
                st.error(f"⚠️ Algolia Sync Failed: {alg_err}")

        return True
    except: return False
    finally: conn.close()

def get_db_suppliers(location):
    """Fetches suppliers. Uses Algolia if available, falls back to SQLite."""
    suppliers = []
    
    # A. TRY ALGOLIA FIRST (Fast, Typo-Tolerant)
    if ALGOLIA_READY:
        try:
            # Algolia search
            res = index_suppliers.search(location) 
            for hit in res['hits']:
                suppliers.append({
                    "name": hit.get("company_name"),
                    "markup": 0.98,
                    "rating": "⭐" * 5,
                    "phone": hit.get("phone"),
                    "email": hit.get("email")
                })
            if suppliers: return suppliers
        except:
            print("Algolia search failed, falling back to SQL.")

    # B. FALLBACK TO SQLITE (Reliable)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM suppliers WHERE location LIKE ?", (f"%{location}%",))
    rows = c.fetchall()
    conn.close()
    
    # Avoid duplicates if fallback runs
    if not suppliers:
        return [{"name": r["company_name"], "markup": 0.98, "rating": "⭐"*int(r["rating"]), "phone": r["phone"], "email": r["email"]} for r in rows]
    
    return suppliers

def get_all_supplier_names():
    """Fetches list of all registered suppliers for the dropdown."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT company_name FROM suppliers")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows] if rows else ["Mubarak Cement (Demo)"]

def update_bid_status(bid_id, new_status):
    """Updates a bid to 'Accepted' or 'Rejected'."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE bids SET status = ? WHERE id = ?", (new_status, bid_id))
    conn.commit()
    conn.close()
    return True

def get_supplier_bids(supplier_name):
    """Gets all bids made by a specific supplier to show them the status."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM bids WHERE supplier_name = ? ORDER BY timestamp DESC", (supplier_name,))
    rows = c.fetchall()
    conn.close()
    return rows

# ==========================================
# 💰 BIDDING ENGINE (ALGOLIA POWERED)
# ==========================================

def get_open_tenders(location_query):
    """Finds projects using Algolia for 'Job Board' search logic."""
    tenders = []
    
    # A. TRY ALGOLIA
    if ALGOLIA_READY:
        try:
            res = index_projects.search(location_query)
            for hit in res['hits']:
                tenders.append({
                    "name": hit.get("name"),
                    "date": hit.get("date_str"),
                    "est_value": hit.get("est_value", 0),
                    "items": len(hit.get("materials_needed", []))
                })
            if tenders: return tenders
        except:
            pass

    # B. FALLBACK TO SQLITE
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, timestamp, boq_json FROM projects WHERE location LIKE ? ORDER BY timestamp DESC", (f"%{location_query}%",))
    rows = c.fetchall()
    conn.close()
    
    if not tenders:
        for r in rows:
            try:
                df = pd.read_json(StringIO(r[2]))
                total_est = df['Total Cost'].sum()
                tenders.append({"name": r[0], "date": r[1], "est_value": total_est, "items": len(df)})
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
# 🚧 EXECUTION (SQLITE ONLY - TRANSACTIONAL)
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

def update_inventory(project, item, quantity, unit, operation):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now_date = datetime.now().strftime("%Y-%m-%d")
    now_time = datetime.now().strftime("%H:%M")
    try:
        c.execute("SELECT quantity FROM inventory WHERE project_name = ? AND item_name = ?", (project, item))
        row = c.fetchone()
        current_qty = row[0] if row else 0.0
        
        if operation == 'add':
            new_qty = current_qty + quantity
            log_qty = quantity; op_label = "Stock IN"
        elif operation == 'remove':
            new_qty = current_qty - quantity
            if new_qty < 0: return False, "Insufficient Stock!"
            log_qty = -quantity; op_label = "Stock OUT"
        
        if row:
            c.execute("UPDATE inventory SET quantity = ?, last_updated = ? WHERE project_name = ? AND item_name = ?", 
                      (new_qty, now_date, project, item))
        else:
            if operation == 'remove': return False, "Item not in inventory!"
            c.execute("INSERT INTO inventory (project_name, item_name, quantity, unit, last_updated) VALUES (?, ?, ?, ?, ?)",
                      (project, item, quantity, unit, now_date))
        
        c.execute('INSERT INTO inventory_logs (project_name, item_name, change_qty, unit, operation, date, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                  (project, item, log_qty, unit, op_label, now_date, now_time))
        
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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT date, timestamp, item_name, operation, change_qty, unit FROM inventory_logs WHERE project_name = ? ORDER BY date DESC, timestamp DESC", (project_name,))
    cols = ["Date", "Time", "Item", "Action", "Change", "Unit"]
    return pd.DataFrame(c.fetchall(), columns=cols)

def log_site_photo(project, image_bytes, caption):
    import os
    folder = f"assets/site_photos/{project}"
    os.makedirs(folder, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    path = f"{folder}/{filename}"
    with open(path, "wb") as f: f.write(image_bytes)
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO site_photos (project_name, image_path, caption, timestamp) VALUES (?, ?, ?, ?)",
              (project, path, caption, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    return True

def get_site_photos(project_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT image_path, caption, timestamp FROM site_photos WHERE project_name = ? ORDER BY timestamp DESC", (project_name,))
    return c.fetchall()

def log_site_diary(project, weather, workers_dict, work_done, issues):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    try:
        c.execute("SELECT id FROM site_diary WHERE project_name = ? AND date = ?", (project, date_str))
        if c.fetchone(): return False, "Diary already submitted for today!"
        c.execute('INSERT INTO site_diary (project_name, date, weather, labor_count, work_done, issues, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                  (project, date_str, weather, json.dumps(workers_dict), work_done, issues, datetime.now().strftime("%H:%M")))
        conn.commit()
        return True, "Site Diary Submitted Successfully!"
    except Exception as e: return False, str(e)
    finally: conn.close()

def get_site_diary(project_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT date, weather, labor_count, work_done, issues FROM site_diary WHERE project_name = ? ORDER BY date DESC", (project_name,))
    rows = c.fetchall()
    conn.close()
    data = []
    for r in rows:
        labor = json.loads(r[2]) if r[2] else {}
        labor_str = ", ".join([f"{k}: {v}" for k, v in labor.items() if v > 0])
        data.append({"Date": r[0], "Weather": r[1], "Labor": labor_str, "Work Done": r[3], "Issues": r[4]})
    return pd.DataFrame(data)