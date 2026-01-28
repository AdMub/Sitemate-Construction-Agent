import pandas as pd
import math

# --- STANDARD LAGOS/NIGERIA LABOR RATES (2026 ESTIMATES) ---
RATES = {
    "MASON_DAY_RATE": 9000,      # Senior Bricklayer/Mason per day
    "LABORER_DAY_RATE": 5000,    # Helper/Serve-man per day
    "IRON_BENDER_TON_RATE": 45000, # Contract price per ton of steel
    "CARPENTER_DAY_RATE": 8500,  # Formwork carpenter
}

def calculate_labor_cost(material_df):
    """
    Analyzes the Material Dataframe and estimates Labor costs 
    based on productivity heuristics.
    """
    if material_df is None or material_df.empty:
        return pd.DataFrame()

    labor_items = []

    # --- 1. BLOCK LAYING LOGIC ---
    # Heuristic: 1 Mason + 1 Laborer can lay ~400 blocks per day.
    blocks_row = material_df[material_df['Item'].str.contains("Block", case=False)]
    if not blocks_row.empty:
        total_blocks = blocks_row['Qty'].sum()
        if total_blocks > 0:
            # Calculate Teams needed
            days_needed = math.ceil(total_blocks / 400)
            
            # Cost for Masons
            labor_items.append({
                "Role": "Masons (Block Laying)",
                "Count": f"{days_needed} Man-Days",
                "Rate": RATES["MASON_DAY_RATE"],
                "Amount": days_needed * RATES["MASON_DAY_RATE"]
            })
            
            # Cost for Laborers (Serving)
            labor_items.append({
                "Role": "Laborers (Serving Blocks)",
                "Count": f"{days_needed} Man-Days",
                "Rate": RATES["LABORER_DAY_RATE"],
                "Amount": days_needed * RATES["LABORER_DAY_RATE"]
            })

    # --- 2. CONCRETE WORK (Casting) ---
    # Heuristic: For every 20 Bags of Cement (approx 3m3), you need a 'Gang' for 1 day.
    # Gang = 1 Mason + 4 Laborers + 1 Carpenter (if columns involved).
    cement_row = material_df[material_df['Item'].str.contains("Cement", case=False)]
    if not cement_row.empty:
        total_cement = cement_row['Qty'].sum()
        if total_cement > 0:
            # Assume 50% of cement is for concrete casting (rest for mortar/plaster)
            casting_cement = total_cement * 0.6 
            gang_days = math.ceil(casting_cement / 20)
            
            labor_items.append({
                "Role": "Concrete Gang (Casting)",
                "Count": f"{gang_days} Gang-Days",
                "Rate": (1 * RATES["MASON_DAY_RATE"]) + (4 * RATES["LABORER_DAY_RATE"]),
                "Amount": gang_days * ((1 * RATES["MASON_DAY_RATE"]) + (4 * RATES["LABORER_DAY_RATE"]))
            })

    # --- 3. IRON BENDING (Reinforcement) ---
    # Heuristic: 1 Length of 12mm Rod ≈ 10.5kg.
    # Benders charge per TON.
    steel_row = material_df[material_df['Item'].str.contains("Iron|Steel", case=False)]
    if not steel_row.empty:
        total_lengths = steel_row['Qty'].sum()
        if total_lengths > 0:
            total_tonnage = (total_lengths * 10.5) / 1000
            # Min charge is usually for 0.5 ton
            chargeable_tons = max(0.5, total_tonnage)
            
            labor_items.append({
                "Role": "Iron Bending Contract",
                "Count": f"{total_tonnage:.2f} Tons",
                "Rate": RATES["IRON_BENDER_TON_RATE"],
                "Amount": chargeable_tons * RATES["IRON_BENDER_TON_RATE"]
            })

    # --- 4. EXCAVATION (Foundation) ---
    # Simple heuristic: Flat rate check based on project size (inferred from cement)
    if not cement_row.empty:
        # Rough proxy: Small projects uses ~50 bags, Big ones ~200+
        # We assign diggers based on "scale"
        diggers_cost = 25000 if total_cement > 100 else 10000
        labor_items.append({
            "Role": "Excavation (Digging)",
            "Count": "Lump Sum",
            "Rate": diggers_cost,
            "Amount": diggers_cost
        })

    return pd.DataFrame(labor_items)