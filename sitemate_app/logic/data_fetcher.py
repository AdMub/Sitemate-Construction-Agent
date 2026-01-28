import requests
import streamlit as st
import random

# ========================================================
# 1️⃣ MOCK DATABASE (For Marketplace Tab)
# ========================================================
SUPPLIER_DB = {
    "Lekki, Lagos": [
        {"name": "Lekki Depot Direct", "markup": 1.0, "rating": "⭐⭐⭐⭐", "phone": "2348145916352", "email": "sales@lekkidepot.ng"},
        {"name": "BuildRight Nigeria", "markup": 1.05, "rating": "⭐⭐⭐⭐⭐", "phone": "2347066502185", "email": "info@buildright.com"},
        {"name": "Express Materials", "markup": 1.10, "rating": "⭐⭐⭐", "phone": "2348123456789", "email": "express@materials.ng"}
    ],
    "Ibadan, Oyo": [
        {"name": "Oyo Concrete Works", "markup": 0.95, "rating": "⭐⭐⭐⭐", "phone": "2348033333333", "email": "orders@oyoworks.ng"},
        {"name": "Bodija Hardware", "markup": 1.02, "rating": "⭐⭐⭐", "phone": "2347031112222", "email": "sales@bodija.com"}
    ],
    "Abuja, FCT": [
        {"name": "FCT Steel & Cement", "markup": 1.08, "rating": "⭐⭐⭐⭐⭐", "phone": "2349159066483", "email": "info@fctsteel.com"},
        {"name": "Abuja Civil Store", "markup": 1.0, "rating": "⭐⭐⭐⭐", "phone": "2348180009999", "email": "contact@abujacivil.com"}
    ]
}

# ========================================================
# 2️⃣ FALLBACK PRICES (Used if API Fails)
# ========================================================
FALLBACK_PRICES = {
    "Lekki, Lagos": {
        "Cement": 11500, "Sharp Sand": 140000, "Granite": 720000, 
        "12mm Iron Rod": 15000, "9-inch Vibrated Block": 650
    },
    "Ibadan, Oyo": {
        "Cement": 10500, "Sharp Sand": 90000, "Granite": 550000, 
        "12mm Iron Rod": 14500, "9-inch Vibrated Block": 500
    },
    "Abuja, FCT": {
        "Cement": 12000, "Sharp Sand": 120000, "Granite": 680000, 
        "12mm Iron Rod": 16000, "9-inch Vibrated Block": 700
    }
}

# ========================================================
# 3️⃣ HELPER FUNCTIONS
# ========================================================
def get_suppliers_for_location(location):
    """Returns list of suppliers for the specific location."""
    return SUPPLIER_DB.get(location, SUPPLIER_DB["Lekki, Lagos"])

def get_live_price(query, location):
    """
    Hybrid Fetcher:
    1. Tries Algolia API first (Real Data).
    2. If API fails, looks up FALLBACK_PRICES (Hardcoded Data).
    """
    price = 0
    name_desc = query
    
    # --- METHOD A: TRY ALGOLIA API ---
    try:
        if "ALGOLIA_API_KEY" in st.secrets:
            APP_ID = st.secrets["ALGOLIA_APP_ID"]
            API_KEY = st.secrets["ALGOLIA_API_KEY"]
            INDEX_NAME = st.secrets.get("ALGOLIA_INDEX_NAME", "construction_materials")
            
            url = f"https://{APP_ID}-dsn.algolia.net/1/indexes/{INDEX_NAME}/query"
            headers = {
                "X-Algolia-Application-Id": APP_ID,
                "X-Algolia-API-Key": API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "query": query,
                "hitsPerPage": 1,
                "optionalWords": query 
            }

            response = requests.post(url, headers=headers, json=payload, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if data['hits']:
                    best_match = data['hits'][0]
                    base_price = best_match.get('price', 0)
                    item_name = best_match.get('name', query)
                    
                    # Apply Logistics Logic (Since DB is likely Ibadan-based)
                    logistics_note = ""
                    if "Lekki" in location or "Lagos" in location:
                        price = base_price * 1.15
                        logistics_note = " (Inc. 15% Transport)"
                    elif "Abuja" in location:
                        price = base_price * 1.25
                        logistics_note = " (Inc. 25% Logistics)"
                    else:
                        price = base_price
                        
                    # Round price
                    price = round(price / 100) * 100
                    name_desc = f"{item_name}{logistics_note}"
                    
                    return price, name_desc
    except Exception:
        # Silently fail to fallback if internet/API is down
        pass

    # --- METHOD B: FALLBACK TO DICTIONARY ---
    # If Algolia failed or returned 0, use the hardcoded dictionary
    if price == 0:
        loc_data = FALLBACK_PRICES.get(location, FALLBACK_PRICES["Lekki, Lagos"])
        
        # Fuzzy match the query to keys in our dictionary
        for key, val in loc_data.items():
            if key.lower() in query.lower() or query.lower() in key.lower():
                price = val
                name_desc = f"{key} (Market Avg)"
                break
                
    return price, name_desc