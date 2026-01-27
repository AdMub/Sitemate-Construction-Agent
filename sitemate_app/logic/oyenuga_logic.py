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
# 2️⃣ THE AI CONNECTOR: GROQ API (LLAMA 3)
# ========================================================
def query_groq_direct(prompt):
    """
    Sends the engineering prompt to Groq.
    """
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        return "❌ Error: GROQ_API_KEY not found in secrets.toml"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are SiteMate, a Senior Structural Engineer. Output strict JSON in ||| pipes |||."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1 
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ Groq Error: {response.status_code}"
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

    # --- Step D: The "Golden Prompt" with STRICT FORMATTING ---
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
    (IMPORTANT: Use these EXACT dimensions in your report).

    [ENGINEERING CONSTANTS]
    1. **Sand/Granite Mixes:** - Standard Mix (1:2:4): 0.6T Sand, 0.9T Granite per m³.
    2. **Steel:** - 1 Length of Y12 = 12 meters = 10.5kg.
    
    [ENGINEERING RULES]
    1. **IF SWAMPY/CLAY:** - Verdict: DANGER. Strip/Pad UNSAFE. Recommend Raft.
    2. **IF FIRM/SANDY:** - Verdict: SAFE. Accept Strip/Pad.
    
    [CRITICAL UNIT CONVERSIONS]
    - **Sand/Granite:** Output TRUCK COUNTS (ceil(Tons / 20) for Sand, ceil(Tons / 30) for Granite).
    - **Steel:** Output LENGTHS (Total Kg / 10.5).
       
    [REPORT STRUCTURE - STRICTLY FOLLOW THIS MARKDOWN FORMAT]
    
    ## 🏗️ Structural Analysis Report
    
    ### 1. Site Safety Verdict ⚠️
    - **Soil Condition:** {effective_soil}
    - **Proposed Design:** (Strip or Pad)
    - **Verdict:** (🔴 UNSAFE / 🟢 SAFE)
    - **Engineering Note:** (Brief explanation from Oyenuga Ch 8).

    ### 2. Design Specifications 📐
    - **Width/Size:** (From Python Engine)
    - **Depth:** (From Python Engine)
    - **Reinforcement:** (From Python Engine)

    ### 3. Material Calculations 🧮
    *Show your working clearly.*
    - **Concrete Volume:** Formula = ... Result = ...
    - **Cement:** ... Bags
    - **Sand/Granite:** ... Tons (Converted to Trucks)

    ### 4. Bill of Quantities (Market Units) 📋
    | Item | Calculated Qty | Market Unit | Procurement Qty |
    | :--- | :--- | :--- | :--- |
    | Cement | ... | 50kg Bag | **X Bags** |
    | Sharp Sand | ... | 20T Truck | **Y Trucks** |
    | Granite | ... | 30T Truck | **Z Trucks** |
    | Iron Rod | ... | 12m Length | **N Lengths** |
    
    [OUTPUT FORMAT]
    End with JSON wrapped in |||. Keys must match exactly.
    Values must be Integers.
    
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
    
    # Clean output (Hide JSON block)
    if ai_text and "|||" in ai_text:
        ai_text = ai_text.split("|||")[0].replace("### JSON", "").strip()
        
    return ai_text, boq_data