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

# --- 2. THE GROQ CONNECTOR (Secure & Direct) ---
def query_groq_direct(prompt):
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        return "❌ Error: GROQ_API_KEY not found in secrets.toml"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    # Using Llama-3.3-70b for maximum reasoning
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are SiteMate, a Senior Structural Engineer. Be concise. Output strict JSON in ||| pipes |||."},
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
    # A. Detect Soil Context
    effective_soil = soil_type
    if "swamp" in user_input.lower():
        effective_soil = "Swampy (Detected from chat)"

    # B. Fetch Market Data
    market_context = fetch_market_context(user_input, location)

    # C. THE MASTER PROMPT (Fixed for Unit Conversion Bugs)
    prompt = f"""
    [CONTEXT]
    Location: {location}
    Soil: {effective_soil}
    Query: "{user_input}"
    
    [PRICES FROM DB]
    {market_context}
    
    [ENGINEERING CONSTANTS]
    1. **Blockwork:** 10 Blocks per m² of wall area. (Standard 9" Block).
       - Fence Calculation: Length x Height x 10.
    2. **Concrete Mixes:**
       - Standard (1:2:4): 6.5 Bags Cement, 0.6T Sand, 0.9T Granite per m³.
       - Raft/Water (1:1.5:3): 8.5 Bags Cement, 0.5T Sand, 0.8T Granite per m³.
    3. **Foundations:**
       - **Swamp/Clay:** REJECT Strip. Use Raft (Vol = Area x 0.25m Bungalow / 0.35m Duplex).
       - **Firm Soil:** Accept Strip. (Vol approx 15-20m³ for standard Bungalow).
    4. **Steel:**
       - 1 Length of Y12 = 12 meters = 10.5kg.
       - Raft Steel = 100kg/m³. Strip Steel = 50kg/m³.
    
    [CRITICAL UNIT CONVERSIONS]
    You must convert raw numbers into "Market Units" for the JSON:
    1. **Sand/Granite:** Convert TONS to TRUCKS. 
       - Formula: ceil(Tons / 20) for Sand. ceil(Tons / 30) for Granite.
       - Example: 30 Tons Granite -> Output "1" (Truck), NOT "30".
    2. **Steel:** Convert KG to LENGTHS.
       - Formula: Total Kg / 10.5 kg.
       - Example: 3,750 kg -> Output "357" (Lengths), NOT "3750".
       
    [TASK]
    1. Analyze Structural Safety.
    2. Calculate Quantities using the Constants above.
    3. Generate a professional Markdown report (No yapping).
    4. **Generate JSON Data.**
    
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

    # D. Call Groq
    ai_text = query_groq_direct(prompt)
    
    # E. Parse Data
    boq_data = extract_json_from_text(ai_text)
    
    # Clean Output
    if ai_text and "|||" in ai_text:
        ai_text = ai_text.split("|||")[0].replace("### JSON", "").strip()
        
    return ai_text, boq_data