import sqlite3
import pandas as pd
import json
from datetime import datetime

DB_FILE = "sitemate_projects.db"

def init_db():
    """Initializes the local SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Create table if not exists
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
    conn.commit()
    conn.close()

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
        conn.close()
        return True, "Project saved successfully!"
    except Exception as e:
        conn.close()
        return False, f"Error: {e}"

def get_all_projects():
    """Returns a list of project names for the dropdown."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, timestamp FROM projects ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows # Returns list of (name, timestamp)

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
        df = pd.read_json(boq_json)
        return location, soil, df
    return None, None, None

def delete_project(name):
    """Deletes a project."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE name=?", (name,))
    conn.commit()
    conn.close()