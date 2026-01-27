import requests
import streamlit as st
import time
import json
import re

# ========================================================
# 📦 MODULE IMPORTS
# ========================================================
from logic.data_fetcher import get_live_price
from logic.structural_engine import StructuralEngine 
from logic.visualizer import render_strip_foundation, render_pad_foundation 

# ========================================================
# 1️⃣ CONTEXT BUILDER: MARKET DATA FETCHER
# ========================================================
def fetch_market_context(user_query, location):
    """
    Fetches live prices from Algolia.
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

# ========================================================
# 2️⃣ THE AI CONNECTOR: LLAMA 3.3 (STABLE & POWERFUL)
# ========================================================
def query_groq_direct(prompt):
    """
    Sends the engineering prompt to Groq using the stable Llama 3.3 model.
    """
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        return "❌ Error: GROQ_API_KEY not found in secrets.toml"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        # SWITCHED TO STABLE FLAGSHIP MODEL
        "model": "llama-3.3-70b-versatile", 
        "messages": [
            {"role": "system", "content": "You are SiteMate, a Senior Structural Engineer. Output strict JSON in ||| pipes |||."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 # Low temperature for precise engineering math
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ Groq Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Connection Error: {e}"

# ========================================================
# 3️⃣ STRUCTURAL ENGINE & VISUALIZATION HELPER
# ========================================================
def run_structural_check(user_input, soil_type):
    """
    Runs Math Engine & Generates Visuals.
    """
    engine = StructuralEngine()
    design_note = ""

    # Define Soil Bearing Capacity (SBC)
    sbc = 150 # Firm soil
    if "swamp" in soil_type.lower():
        sbc = 50 # Swamp

    # --- SCENARIO A: PAD FOUNDATION ---
    if "pad" in user_input.lower():
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
        
        st.markdown(f"#### 📐 Structural Blueprint: {result['type']}")
        fig = render_pad_foundation(result['size_mm'], result['depth_mm'])
        st.pyplot(fig) 

    # --- SCENARIO B: STRIP FOUNDATION ---
    elif "strip" in user_input.lower():
        load = 100 
        result = engine.design_strip_foundation(load, sbc)
        
        design_note = f"""
        **🐍 PYTHON STRUCTURAL ENGINE OUTPUT:**
        - **Design:** {result['type']}
        - **Calculated Width:** {result['width_mm']}mm
        - **Depth:** {result['depth_mm']}mm
        - **Reinforcement:** {result['reinforcement']}
        """
        
        st.markdown(f"#### 📐 Structural Blueprint: {result['type']}")
        fig = render_strip_foundation(result['width_mm'], result['depth_mm'])
        st.pyplot(fig) 
        
    return design_note

# ========================================================
# 4️⃣ UTILITY: JSON PARSER
# ========================================================
def extract_json_from_text(text):
    try:
        match = re.search(r'\|\|\|(.*?)\|\|\|', text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
    except:
        pass
    return None

# ========================================================
# 5️⃣ THE MAIN AGENT (ORCHESTRATOR)
# ========================================================
def get_agent_response(user_input, location, soil_type):
    """
    The Master Function that coordinates Context, Logic, Visuals, and AI.
    """
    
    # --- 🛑 INTENT GUARD ---
    clean_input = user_input.lower().strip()
    if len(clean_input.split()) < 3 or "cancel" in clean_input or "mistake" in clean_input:
        return "🛑 **Recording Ignored.** I detected a cancellation or unclear audio. Please record again.", None

    # --- Step A: Sidebar Context ---
    effective_soil = soil_type
    if "swamp" in user_input.lower():
        effective_soil = "Swampy (User overrode via Chat)"
    elif "firm" in user_input.lower():
        effective_soil = "Firm/Sandy (User overrode via Chat)"

    # --- Step B: Market Data ---
    market_context = fetch_market_context(user_input, location)

    # --- Step C: Math & Visuals ---
    structural_calc_result = run_structural_check(user_input, effective_soil)

    # --- Step D: The "Golden Prompt" ---
    prompt = f"""
    [CRITICAL SITE CONTEXT]
    Location: {location}
    **SOIL CONDITION:** {effective_soil} 
    
    [USER QUERY]
    "{user_input}"
    
    [PRICES FROM DB]
    {market_context}
    
    [PYTHON STRUCTURAL ENGINE RESULTS]
    {structural_calc_result}
    
    [ENGINEERING RULES OF THUMB (USE THESE IF ENGINE FAILS)]
    If the user asks for a **Building** (Hostel, Duplex, etc.) and the Python Engine did not provide exact specs, use these estimates:
    1. **Blocks:** Approx **600 blocks** per standard room (4 walls).
    2. **Concrete (Lintels/Columns):** Approx **0.5m³** concrete per room.
    3. **Foundation (Pad):** Assume 1 Pad per 3m span. Pad size 1.2m x 1.2m x 0.3m.
    4. **Cement Ratio:** 1m³ Concrete = **7 Bags** of Cement.
    5. **Decking (Slab):** 1m² of slab = 1 Bag of Cement approx (for 150mm thick).
    
    [CRITICAL UNIT CONVERSIONS]
    - **Sand/Granite:** Output TRUCK COUNTS (ceil(Tons / 20) for Sand, ceil(Tons / 30) for Granite).
    - **Steel:** Output LENGTHS (Total Kg / 10.5).
       
    [REPORT STRUCTURE]
    
    ## 🏗️ Structural Analysis Report
    
    ### 1. Site Safety Verdict ⚠️
    - **Soil Condition:** {effective_soil}
    - **Proposed Design:** (Strip or Pad)
    - **Verdict:** (🔴 UNSAFE / 🟢 SAFE)
    - **Engineering Note:** (Brief explanation).

    ### 2. Design Estimates 📐
    *Note: These are preliminary estimates based on standard building heuristics.*
    - **Estimated Footprint:** (Length x Width)
    - **Total Rooms:** (From User)
    - **Foundation Strategy:** (e.g., Pads at 3m centers)

    ### 3. Material Calculations 🧮
    *Show your working clearly using the Rules of Thumb.*
    - **Blocks:** ... Rooms x 600 = ...
    - **Concrete:** ...
    - **Cement:** ...

    ### 4. Bill of Quantities (Market Units) 📋
    | Item | Calculated Qty | Market Unit | Procurement Qty |
    | :--- | :--- | :--- | :--- |
    | Cement | ... | 50kg Bag | **X Bags** |
    | Sharp Sand | ... | 20T Truck | **Y Trucks** |
    | Granite | ... | 30T Truck | **Z Trucks** |
    | Iron Rod | ... | 12m Length | **N Lengths** |
    | Vibrated Block | ... | 9-inch Unit | **B Blocks** |
    
    > **⚠️ Professional Disclaimer:** This Bill of Quantities is a Preliminary Estimate based on BS 8110 Empirical Standards and provided for budgeting purposes only. Final construction requires detailed structural drawings approved by a COREN-registered engineer.
    
    [OUTPUT FORMAT]
    End with JSON wrapped in |||. Keys must match exactly.
    Values must be Integers.
    
    |||
    {{
      "Cement": 100,
      "Sharp Sand": 5,
      "Granite": 5,
      "12mm Iron Rod": 200,
      "9-inch Vibrated Block": 5000
    }}
    |||
    """

    # --- Step E: Call AI & Parse Result ---
    ai_text = query_groq_direct(prompt)
    boq_data = extract_json_from_text(ai_text)
    
    if ai_text and "|||" in ai_text:
        ai_text = ai_text.split("|||")[0].replace("### JSON", "").strip()
        
    return ai_text, boq_data