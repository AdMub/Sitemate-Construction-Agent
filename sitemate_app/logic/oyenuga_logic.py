import requests
import streamlit as st
import time
import json
import re
from logic.data_fetcher import get_live_price

# --- 1. CONTEXT BUILDER ---
def fetch_market_context(user_query, location):
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

# --- 2. THE GROQ CONNECTOR ---
def query_groq_direct(prompt):
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

def extract_json_from_text(text):
    try:
        match = re.search(r'\|\|\|(.*?)\|\|\|', text, re.DOTALL)
        if match: return json.loads(match.group(1).strip())
    except: pass
    return None

# --- 3. THE MAIN AGENT ---
def get_agent_response(user_input, location, soil_type):
    # A. PRIORITIZE SIDEBAR
    # Logic: The Sidebar is the 'Source of Truth'. 
    # We only update if the user explicitly overrides it in the chat.
    effective_soil = soil_type
    
    if "swamp" in user_input.lower():
        effective_soil = "Swampy (User overrode via Chat)"
    elif "firm" in user_input.lower():
        effective_soil = "Firm/Sandy (User overrode via Chat)"

    # B. Fetch Market Data
    market_context = fetch_market_context(user_input, location)

    # C. THE MASTER PROMPT (Integrates Sidebar Logic + Unit Conversion Fixes)
    prompt = f"""
    [CRITICAL SITE CONTEXT]
    Location: {location}
    **SOIL CONDITION:** {effective_soil} 
    (Note: You MUST base all safety verdicts on this Soil Condition above).
    
    [USER QUERY]
    "{user_input}"
    
    [PRICES FROM DB]
    {market_context}
    
    [ENGINEERING CONSTANTS]
    1. **Sand/Granite:** - Standard Mix (1:2:4): 0.6T Sand, 0.9T Granite per m³.
       - Raft Mix (1:1.5:3): 0.5T Sand, 0.8T Granite per m³.
    2. **Steel:** - 1 Length of Y12 = 12 meters = 10.5kg.
       - Raft Steel = 100kg/m³. Strip Steel = 50kg/m³.
    
    [ENGINEERING RULES]
    1. IF SOIL IS SWAMPY/CLAY:
       - **Verdict:** REJECT Strip Foundation. REJECT Pad Foundation.
       - **Action:** MUST calculate for Raft Foundation (Vol = Area x 0.25m).
    2. IF SOIL IS FIRM/SANDY:
       - **Verdict:** ACCEPT Strip Foundation.
    
    [CRITICAL UNIT CONVERSIONS]
    1. **Sand/Granite:** Output TRUCK COUNTS. (Formula: ceil(Tons / 20) for Sand, ceil(Tons / 30) for Granite).
    2. **Steel:** Output LENGTHS. (Formula: Total Kg / 10.5).
       
    [TASK]
    1. Check if the User's request matches the Soil Condition ({effective_soil}). Warn them if it's unsafe.
    2. Calculate Quantities.
    3. Generate a Markdown report.
    4. Generate JSON Data.
    
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

    # D. Call Groq
    ai_text = query_groq_direct(prompt)
    
    # E. Parse Data
    boq_data = extract_json_from_text(ai_text)
    
    # Clean Output
    if ai_text and "|||" in ai_text:
        ai_text = ai_text.split("|||")[0].replace("### JSON", "").strip()
        
    return ai_text, boq_data