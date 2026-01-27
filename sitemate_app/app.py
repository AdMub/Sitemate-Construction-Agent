import streamlit as st
import pandas as pd
import altair as alt
import time

# --- IMPORT CUSTOM LOGIC ---
from logic.oyenuga_logic import get_agent_response
from logic.data_fetcher import get_live_price 

# 1. PAGE CONFIG
st.set_page_config(page_title="SiteMate Pro", page_icon="🏗️", layout="wide")
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# 2. SIDEBAR
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=60)
    st.title("SiteMate Pro")
    st.caption("v3.0 | Licensed to: **Lekki Projects Ltd**")
    st.divider()
    
    st.subheader("📍 Site Context")
    location = st.selectbox("Project Location", ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"])
    soil_type = st.select_slider("Soil Condition", options=["Firm/Sandy", "Clay", "Swampy"])
    st.divider()
    
    # LIVE BUDGET METRIC
    if 'total_actual' in st.session_state:
        val = st.session_state['total_actual']
        label = "Live Project Budget"
        if val > 1000000: # If over 1 million, it's a full project, not just unit prices
            label = "Total Project Estimate"
            
        st.metric(label=label, value=f"₦ {val:,.0f}", delta="Synced with Chat")
    else:
        st.metric(label="Live Project Budget", value="--")

# 3. MAIN WORKSPACE
st.title("🏗️ Engineering Command Center")
tab1, tab2, tab3 = st.tabs(["💬 Engineering Chat", "📊 Cost Dashboard", "🛒 Procurement (PO)"])

# --- TAB 1: CHAT (The Source) ---
with tab1:
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input("Ask SiteMate..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing structural requirements..."):
                
                # GET RESPONSE + DATA
                response_text, boq_data = get_agent_response(prompt, location, soil_type)
                
                st.markdown(response_text)
                
                # --- THE HANDOVER PROTOCOL ---
                # If Chat generated a BOQ, send it to Session State for Tab 2 & 3
                if boq_data:
                    st.session_state['active_boq'] = boq_data
                    st.success("✅ Bill of Quantities sent to **Cost Dashboard**.")
                else:
                    # If no specific project, clear previous BOQ to show unit prices
                    if 'active_boq' in st.session_state:
                        del st.session_state['active_boq']

        st.session_state.messages.append({"role": "assistant", "content": response_text})

# --- TAB 2: DASHBOARD (The Calculator) ---
with tab2:
    col_header, col_btn = st.columns([4,1])
    with col_header:
        # Dynamic Header
        if 'active_boq' in st.session_state:
            st.subheader(f"📊 Project Bill of Quantities ({location})")
            st.caption("Quantities derived from Engineering Chat • Prices from Algolia")
        else:
            st.subheader(f"📉 Market Unit Rates ({location})")

    with col_btn:
        refresh = st.button("🔄 Update Costs", type="primary")

    if refresh or 'active_boq' in st.session_state:
        # Determine which items to track
        # If BOQ exists from chat, use that. Otherwise use default list.
        if 'active_boq' in st.session_state:
            target_items = st.session_state['active_boq'] # Dict: {'Cement': 335, ...}
        else:
            target_items = {
                "Cement": 1, "Sharp Sand": 1, "Granite": 1, 
                "12mm Iron Rod": 1, "9-inch Vibrated Block": 1
            }

        live_data = []
        total_act = 0
        
        for item_name, quantity in target_items.items():
            if quantity > 0:
                # Fetch Unit Price
                unit_price, full_name = get_live_price(item_name, location)
                
                # Calculate Line Total
                line_total = unit_price * quantity
                
                if unit_price == 0: full_name = f"⚠️ {item_name} (Not in DB)"
                
                live_data.append({
                    "Item": item_name,
                    "Description": full_name,
                    "Qty": quantity,
                    "Unit Price": unit_price,
                    "Total Cost": line_total
                })
                total_act += line_total

        # Save results
        df = pd.DataFrame(live_data)
        st.session_state['boq_df'] = df
        st.session_state['total_actual'] = total_act

    # Display Logic
    if 'boq_df' in st.session_state:
        df = st.session_state['boq_df']
        
        # Big Metrics
        c1, c2 = st.columns(2)
        c1.metric("Total Project Cost", f"₦{df['Total Cost'].sum():,.0f}")
        c2.metric("Logistics Zone", location)

        # Bar Chart
        chart = alt.Chart(df).mark_bar().encode(
            x='Item',
            y='Total Cost',
            color=alt.value("#FF8C00"),
            tooltip=['Item', 'Qty', 'Total Cost']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
        
        # Detailed Table
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Start a chat in **Tab 1** to generate a Bill of Quantities, or click Refresh to see Unit Prices.")

# --- TAB 3: PROCUREMENT (The Output) ---
with tab3:
    st.subheader("🛒 Procurement Orders")
    
    if 'boq_df' in st.session_state:
        df = st.session_state['boq_df']
        
        # Only show valid items
        valid_orders = df[df['Total Cost'] > 0]
        
        st.markdown(f"**Project Location:** {location}")
        st.dataframe(valid_orders[['Description', 'Qty', 'Unit Price', 'Total Cost']], use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
             st.info(f"**Total Payable:** ₦{valid_orders['Total Cost'].sum():,.0f}")
        with col2:
             if st.button("🚀 Process Purchase Orders"):
                 with st.spinner("Generating Invoices..."):
                     time.sleep(2)
                 st.success("Orders sent to suppliers!")
                 st.balloons()
    else:
        st.warning("⚠️ No active project found. Please chat with SiteMate to create a BOQ.")