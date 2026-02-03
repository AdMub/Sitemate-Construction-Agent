import sqlite3
import pandas as pd
import json
from datetime import datetime

DB_FILE = "sitemate_projects.db"

def init_db():
    """Initializes the database with Projects and Suppliers tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Projects Table (For Users Saving BOQs)
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            location TEXT,
            soil TEXT,
            boq_json TEXT,
            timestamp TEXT
        )
    ''')
    
    # 2. Suppliers Table (For Vendors Registering)
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            location TEXT,
            phone TEXT,
            email TEXT,
            materials TEXT, -- Stored as JSON string
            rating REAL DEFAULT 5.0,
            timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# ==========================================
# 🏗️ PROJECT FUNCTIONS (User Side)
# ==========================================

def save_project(name, location, soil, boq_df):
    """Saves the current project state."""
    if boq_df is None or boq_df.empty:
        return False, "Cannot save empty project."
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Convert DataFrame to JSON string for storage
    boq_json = boq_df.to_json()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    try:
        # Insert or Replace (Update if name exists)
        c.execute('''
            INSERT OR REPLACE INTO projects (name, location, soil, boq_json, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, location, soil, boq_json, date_str))
        conn.commit()
        return True, "Project saved successfully!"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()

def get_all_projects():
    """Returns a list of project names for the dropdown."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, timestamp FROM projects ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows 

def load_project_data(name):
    """Loads a specific project."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT location, soil, boq_json FROM projects WHERE name=?", (name,))
    row = c.fetchone()
    conn.close()
    
    if row:
        location, soil, boq_json = row
        # Reconstruct DataFrame
        try:
            df = pd.read_json(boq_json)
            return location, soil, df
        except:
            return None, None, None
    return None, None, None

def delete_project(name):
    """Deletes a project."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE name=?", (name,))
    conn.commit()
    conn.close()

# ==========================================
# 👷 SUPPLIER FUNCTIONS (Vendor Side)
# ==========================================

def register_supplier(name, location, phone, email, materials_list):
    """Registers a new supplier in the database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d")
    materials_json = json.dumps(materials_list) # Convert list to string
    
    try:
        c.execute('''
            INSERT INTO suppliers (company_name, location, phone, email, materials, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, location, phone, email, materials_json, date_str))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Error: {e}")
        return False
    finally:
        conn.close()

def get_db_suppliers(location):
    """Fetches suppliers from DB for a specific location."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # Access columns by name
    c = conn.cursor()
    
    # Simple partial match for location (e.g. "Lagos" matches "Lekki, Lagos")
    search_term = f"%{location}%"
    
    c.execute("SELECT * FROM suppliers WHERE location LIKE ?", (search_term,))
    rows = c.fetchall()
    conn.close()
    
    suppliers = []
    for row in rows:
        suppliers.append({
            "name": row["company_name"],
            "markup": 0.98, # DB suppliers get a competitive default markup
            "rating": "⭐" * int(row["rating"]),
            "phone": row["phone"],
            "email": row["email"]
        })
    return suppliers