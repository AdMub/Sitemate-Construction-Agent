import requests
import streamlit as st
import time
import json
import re

# --- Custom Module Imports ---
from logic.data_fetcher import get_live_price
from logic.structural_engine import StructuralEngine  # The "Mini-Orion" Engine

# ==========================================
# 1. CONTEXT BUILDER (Market Data)
# ==========================================
def fetch_market_context(user_query, location):
    """
    Fetches live prices from Algolia for key construction materials 
    in the specified location.
    """
    items_to_check = ["Cement", "Granite", "Sharp Sand", "12mm Iron Rod", "9-inch Vibrated Block"]
    context_text = f"**LIVE MARKET DATA FOR {location.upper()}:**\n"
    
    found_data = False
    for item in items_to_check:
        price, name = get_live_price(item, location)
        if price > 0:
            context_text += f"- {name}: ₦{price:,.0f}\n"
            found_data = True
            
    if not found_data:
        return "Market Data Unavailable"
    return context_text

# ==========================================
# 2. THE GROQ CONNECTOR (AI Brain)
# ==========================================
def query_groq_direct(prompt):
    """
    Sends the engineering prompt to Groq's Llama-3 model.
    Includes error handling for API keys and connection issues.
    """
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        return "❌ Error: GROQ_API_KEY not found in secrets.toml"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # We use Llama-3.3-70b for maximum reasoning capability
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are SiteMate, a Senior Structural Engineer. Output strict JSON in ||| pipes |||."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 # Low temperature for precise engineering math
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ Groq Error: {response.status_code}"
    except Exception as e:
        return f"❌ Connection Error: {e}"

# ==========================================
# 3. STRUCTURAL ENGINE HELPER (Deterministic Math)
# ==========================================
def run_structural_check(user_input, soil_type):
    """
    Parses user input for 'Pad' or 'Strip' keywords and runs 
    the Python StructuralEngine to get exact dimensions (BS 8110 standards).
    """
    engine = StructuralEngine()
    design_note = ""

    # Define Soil Bearing Capacity (SBC) based on Sidebar Context
    sbc = 150 # Default: Firm soil (kN/m2)
    if "swamp" in soil_type.lower():
        sbc = 50 # Swamp (Poor bearing capacity)

    # --- Scenario A: User wants a Pad Foundation ---
    if "pad" in user_input.lower():
        # Heuristic: Assume 600kN load for a standard duplex column if not specified
        load = 600 
        result = engine.design_pad_foundation(load, sbc)
        
        design_note = f"""
        **🐍 PYTHON STRUCTURAL ENGINE OUTPUT:**
        - **Design:** {result['type']}
        - **Calculated Size:** {result['size_mm']}
        - **Depth:** {result['depth_mm']}mm
        - **Reinforcement:** {result['reinforcement']}
        - **Concrete Vol:** {result['concrete_vol']} m³ per pad
        """

    # --- Scenario B: User wants a Strip Foundation ---
    elif "strip" in user_input.lower():
        # Heuristic: Assume 100kN/m linear load for a wall
        load = 100
        result = engine.design_strip_foundation(load, sbc)
        
        design_note = f"""
        **🐍 PYTHON STRUCTURAL ENGINE OUTPUT:**
        - **Design:** {result['type']}
        - **Calculated Width:** {result['width_mm']}mm
        - **Depth:** {result['depth_mm']}mm
        - **Reinforcement:** {result['reinforcement']}
        """
        
    return design_note

# ==========================================
# 4. UTILITY: JSON PARSER
# ==========================================
def extract_json_from_text(text):
    """
    Extracts the hidden JSON block wrapped in ||| pipes from the AI response.
    """
    try:
        match = re.search(r'\|\|\|(.*?)\|\|\|', text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
    except:
        pass
    return None

# ==========================================
# 5. THE MAIN AGENT (Orchestrator)
# ==========================================
def get_agent_response(user_input, location, soil_type):
    """
    The Master Function that coordinates Context, Math, and AI.
    """
    
    # --- Step A: Prioritize Sidebar Context (Source of Truth) ---
    effective_soil = soil_type
    
    # Allow user to override sidebar only if explicitly stated in chat
    if "swamp" in user_input.lower():
        effective_soil = "Swampy (User overrode via Chat)"
    elif "firm" in user_input.lower():
        effective_soil = "Firm/Sandy (User overrode via Chat)"

    # --- Step B: Fetch Live Prices ---
    market_context = fetch_market_context(user_input, location)

    # --- Step C: Run Python Structural Engine ---
    # This generates exact dimensions if Pad/Strip is requested
    structural_calc_result = run_structural_check(user_input, effective_soil)

    # --- Step D: Construct the Master Prompt ---
    prompt = f"""
    [CRITICAL SITE CONTEXT]
    Location: {location}
    **SOIL CONDITION:** {effective_soil} 
    (Note: You MUST base all safety verdicts on this Soil Condition).
    
    [USER QUERY]
    "{user_input}"
    
    [PRICES FROM DB]
    {market_context}
    
    [PYTHON STRUCTURAL ENGINE RESULTS]
    {structural_calc_result}
    (IMPORTANT: If Engine results are present above, use these EXACT dimensions and reinforcement specs in your report).

    [ENGINEERING CONSTANTS]
    1. **Sand/Granite Mixes:** - Standard Mix (1:2:4): 0.6T Sand, 0.9T Granite per m³.
       - Raft Mix (1:1.5:3): 0.5T Sand, 0.8T Granite per m³.
    2. **Steel:** - 1 Length of Y12 = 12 meters = 10.5kg.
    
    [ENGINEERING RULES - SAFETY & ECONOMY]
    1. **IF SWAMPY/CLAY:** - **Verdict:** DANGER. Strip or Pad foundations are UNSAFE.
       - **Action:** MUST recommend Raft Foundation (Vol = Area x 0.25m).
    2. **IF FIRM/SANDY:** - **Verdict:** SAFE. Accept Strip or Pad.
       - **Action:** Use Python Engine results if available.
       - **Estimate:** Strip Vol is approx 15-20m³ for standard Bungalow (if not calculated by Engine).
    
    [CRITICAL UNIT CONVERSIONS]
    You must convert raw numbers into "Market Units" for the JSON:
    1. **Sand/Granite:** Output TRUCK COUNTS. 
       - Formula: ceil(Tons / 20) for Sand, ceil(Tons / 30) for Granite.
    2. **Steel:** Output LENGTHS. 
       - Formula: Total Kg / 10.5.
       
    [TASK]
    1. Analyze Soil Safety (Firm vs Swamp).
    2. Calculate Quantities (Use Engine Dimensions if available).
    3. Generate a Markdown report including the "Engine Results".
    4. Generate JSON Data.
    
    [OUTPUT FORMAT]
    End with JSON wrapped in |||. Keys must match exactly.
    Values must be Integers (Truck counts or Rod Lengths).
    
    |||
    {{
      "Cement": 335,
      "Sharp Sand": 2,
      "Granite": 2,
      "12mm Iron Rod": 357,
      "9-inch Vibrated Block": 1500
    }}
    |||
    """

    # --- Step E: Call AI & Parse Result ---
    ai_text = query_groq_direct(prompt)
    boq_data = extract_json_from_text(ai_text)
    
    # Clean the AI text output (Remove the JSON block for display)
    if ai_text and "|||" in ai_text:
        ai_text = ai_text.split("|||")[0].replace("### JSON", "").strip()
        
    return ai_text, boq_data