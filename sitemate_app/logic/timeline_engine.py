import pandas as pd
from datetime import date, timedelta

def calculate_project_timeline(boq_df):
    """
    Generates a project schedule based on material quantities.
    Returns a DataFrame suitable for a Gantt Chart.
    """
    if boq_df is None or boq_df.empty:
        return pd.DataFrame()

    tasks = []
    # Start the project "Today"
    current_date = date.today()

    # --- PHASE 1: SITE PREPARATION (Fixed) ---
    # Every project needs clearing/setting out
    prep_days = 2
    tasks.append({
        "Phase": "1. Site Preparation",
        "Start": current_date,
        "End": current_date + timedelta(days=prep_days),
        "Duration": f"{prep_days} Days"
    })
    # Move timeline forward
    current_date += timedelta(days=prep_days)

    # --- PHASE 2: FOUNDATION (Based on Cement/Sand) ---
    # Heuristic: If we have concrete materials, we likely have a foundation
    has_concrete = boq_df['Item'].str.contains('Cement|Sand|Granite', case=False).any()
    
    if has_concrete:
        # Standard foundation takes about 1 week for a small/medium project
        found_days = 7 
        tasks.append({
            "Phase": "2. Foundation & Substructure",
            "Start": current_date,
            "End": current_date + timedelta(days=found_days),
            "Duration": f"{found_days} Days"
        })
        current_date += timedelta(days=found_days)

    # --- PHASE 3: BLOCK WORK (Based on Block Qty) ---
    blocks_row = boq_df[boq_df['Item'].str.contains("Block", case=False)]
    if not blocks_row.empty:
        total_blocks = blocks_row['Qty'].sum()
        if total_blocks > 0:
            # Heuristic: 2 Masons lay ~800 blocks/day combined. 
            # We add a buffer of 20% for curing/delays.
            daily_rate = 800
            days_needed = int((total_blocks / daily_rate) * 1.2)
            days_needed = max(3, days_needed) # Minimum 3 days for small walls
            
            tasks.append({
                "Phase": "3. Superstructure (Block Work)",
                "Start": current_date,
                "End": current_date + timedelta(days=days_needed),
                "Duration": f"{days_needed} Days"
            })
            current_date += timedelta(days=days_needed)

    # --- PHASE 4: ROOFING & LINTEL (Fixed if Blocks exist) ---
    if not blocks_row.empty:
        roof_days = 7 # Standard 1 week for carpentry + roofing sheets
        tasks.append({
            "Phase": "4. Lintel & Roofing",
            "Start": current_date,
            "End": current_date + timedelta(days=roof_days),
            "Duration": f"{roof_days} Days"
        })
        current_date += timedelta(days=roof_days)

    return pd.DataFrame(tasks)