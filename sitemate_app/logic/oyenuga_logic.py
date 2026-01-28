#### (The Main Brain - Short and Clean now).

import requests
import streamlit as st
from logic.data_fetcher import get_live_price
from logic.structural_engine import StructuralEngine 
from logic.visualizer import render_strip_foundation, render_pad_foundation 
# Import the new modules
from logic.prompts import get_structural_prompt
from logic.utils import extract_json_from_text, clean_ai_text

def fetch_market_context(location):
    """Gets prices for the prompt context."""
    items = ["Cement", "Granite", "Sharp Sand", "12mm Iron Rod", "9-inch Vibrated Block"]
    context = f"**LIVE MARKET DATA FOR {location.upper()}:**\n"
    found = False
    for item in items:
        price, name = get_live_price(item, location)
        if price > 0:
            context += f"- {name}: ₦{price:,.0f}\n"
            found = True
    return context if found else "Market Data Unavailable"

def query_groq_direct(prompt):
    """Talks to the AI."""
    try:
        api_key = st.secrets["GROQ_API_KEY"]
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
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return f"❌ Groq Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Connection Error: {e}"

def get_agent_response(user_input, location, soil_type):
    """Main Orchestrator function called by app.py."""
    
    # 1. Intent Guard
    if len(user_input.split()) < 2:
         return "Please provide more details (e.g., 'Budget for a fence' or '2 bedroom flat').", None

    # 2. Setup Logic
    engine = StructuralEngine()
    effective_soil = "Swampy (User Override)" if "swamp" in user_input.lower() else soil_type
    
    # 3. Structural Calculation (Visuals)
    calc_note = ""
    if "pad" in user_input.lower():
        res = engine.design_pad_foundation(600, 150)
        calc_note = f"Engine: Pad Size {res['size_mm']}"
        st.markdown(f"#### 📐 Structural Blueprint: {res['type']}")
        st.pyplot(render_pad_foundation(res['size_mm'], res['depth_mm']))
        
    elif "strip" in user_input.lower() or "fence" in user_input.lower():
        res = engine.design_strip_foundation(100, 150)
        calc_note = f"Engine: Strip Width {res['width_mm']}mm"
        # Only draw if explicitly asked
        if "draw" in user_input.lower() or "sketch" in user_input.lower() or "diagram" in user_input.lower():
            st.markdown(f"#### 📐 Structural Blueprint: {res['type']}")
            st.pyplot(render_strip_foundation(res['width_mm'], res['depth_mm']))

    # 4. Build Prompt
    market_data = fetch_market_context(location)
    full_prompt = get_structural_prompt(location, effective_soil, market_data, calc_note)
    full_prompt += f'\n[USER QUERY]\n"{user_input}"'

    # 5. Execute AI
    raw_response = query_groq_direct(full_prompt)
    
    # 6. Parse Results
    boq_data = extract_json_from_text(raw_response)
    clean_text = clean_ai_text(raw_response)
        
    return clean_text, boq_data