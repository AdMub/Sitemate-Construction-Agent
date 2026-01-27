import requests
import streamlit as st

def get_live_price(query, location):
    """
    Fetches the Base Price from Algolia (Ibadan data) and applies 
    Logistics Multipliers based on the project location.
    """
    try:
        # 1. Credentials
        APP_ID = st.secrets["ALGOLIA_APP_ID"]
        API_KEY = st.secrets["ALGOLIA_API_KEY"]
        INDEX_NAME = st.secrets.get("ALGOLIA_INDEX_NAME", "construction_materials")
        
        url = f"https://{APP_ID}-dsn.algolia.net/1/indexes/{INDEX_NAME}/query"
        
        headers = {
            "X-Algolia-Application-Id": APP_ID,
            "X-Algolia-API-Key": API_KEY,
            "Content-Type": "application/json"
        }

        # 2. Search Payload (Generic search to find the item)
        payload = {
            "query": query,
            "hitsPerPage": 1,
            "optionalWords": query 
        }

        response = requests.post(url, headers=headers, json=payload, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data['hits']:
                best_match = data['hits'][0]
                base_price = best_match.get('price', 0)
                name = best_match.get('name', 'Unknown')
                supplier = best_match.get('supplier', 'General Market')
                
                # 3. APPLY LOGISTICS LOGIC
                # Database = Ibadan Prices. We adjust for other cities.
                
                final_price = base_price
                logistics_note = ""

                if "Lekki" in location or "Lagos" in location:
                    # +15% for Transport to Lagos
                    final_price = base_price * 1.15
                    logistics_note = " (Inc. 15% Transport)"
                elif "Abuja" in location:
                    # +25% for Long Haul Logistics
                    final_price = base_price * 1.25
                    logistics_note = " (Inc. 25% Logistics)"
                
                # Round to nearest 100 Naira for cleanliness
                final_price = round(final_price / 100) * 100
                
                return final_price, f"{name}{logistics_note}"
            else:
                return 0, "❌ Not Found"
        else:
            return 0, f"API Error {response.status_code}"
            
    except Exception:
        return 0, "Connection Failed"