import streamlit as st
import pandas as pd
import altair as alt
import time
import urllib.parse  # Required for WhatsApp Link Generation

# --- 1. IMPORTS ---
from streamlit_mic_recorder import mic_recorder
from logic.transcriber import transcribe_audio
from logic.oyenuga_logic import get_agent_response
from logic.data_fetcher import get_live_price
from logic.report_generator import generate_pdf_report

# 2. PAGE CONFIG
st.set_page_config(page_title="SiteMate Pro", page_icon="🏗️", layout="wide")
try:
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except:
    pass 

# 3. SIDEBAR
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=60)
    st.title("SiteMate Pro")
    st.caption("v4.0 | Licensed to: **Lekki Projects Ltd**")
    st.divider()
    
    # --- FEATURE 5: SMART GEOLOCATION & SOIL MAP ---
    st.subheader("📍 Site Context")
    
    # Define the mapping logic (Location -> Default Soil)
    SOIL_DEFAULTS = {
        "Lekki, Lagos": "Swampy",
        "Ibadan, Oyo": "Firm/Sandy",
        "Abuja, FCT": "Firm/Sandy"
    }
    
    # Location Selectbox
    selected_loc = st.selectbox(
        "Project Location", 
        ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"],
        key="loc_selector"
    )
    
    # Auto-update logic: If location changes, update soil default
    if "last_location" not in st.session_state or st.session_state.last_location != selected_loc:
        st.session_state.last_location = selected_loc
        st.session_state.soil_default = SOIL_DEFAULTS[selected_loc]

    # Soil Slider (Controlled by session state but editable)
    soil_type = st.select_slider(
        "Soil Condition", 
        options=["Firm/Sandy", "Clay", "Swampy"],
        value=st.session_state.get("soil_default", "Firm/Sandy")
    )
    
    # Visual Feedback for Automation
    if soil_type == SOIL_DEFAULTS[selected_loc]:
        st.caption(f"✨ *Auto-detected soil for {selected_loc.split(',')[0]}*")
    
    st.divider()

    # --- FEATURE 4: WHAT-IF SCENARIOS ---
    with st.expander("⚡ What-If Scenarios", expanded=True):
        st.caption("Adjust parameters to see instant cost impact.")
        
        # 1. Steel Volatility Slider
        steel_var = st.slider("📉 Steel Price Variance", -10, 20, 0, format="%d%%")
        
        # 2. Concrete Grade Switch
        concrete_grade = st.radio("🏗️ Concrete Grade", ["M20 (Standard)", "M25 (Heavy Duty)"])
        
        if concrete_grade == "M25 (Heavy Duty)":
            st.caption("ℹ️ *M25 requires ~25% more cement.*")
        if steel_var != 0:
            st.caption(f"ℹ️ *Steel adjusted by {steel_var}%.*")

    st.divider()
    
    # --- FEATURE 3: PDF EXPORT (WITH DATAFRAME FIX) ---
    # We check for 'boq_df' (The calculated financial table)
    if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
        st.subheader("📄 Export")
        
        pdf_bytes = generate_pdf_report(
            user_query=st.session_state.get('last_user_query', 'N/A'),
            location=selected_loc,
            soil_type=soil_type,
            ai_text=st.session_state.get('last_ai_response', ''),
            boq_dataframe=st.session_state['boq_df']  # <--- CRITICAL: Sending the priced dataframe
        )
        
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name=f"SiteMate_Report_{int(time.time())}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        st.divider()

    # LIVE BUDGET METRIC
    if 'total_actual' in st.session_state:
        st.metric(label="Live Project Budget", value=f"₦ {st.session_state['total_actual']:,.0f}")
    else:
        st.metric(label="Live Project Budget", value="--")

# 4. MAIN WORKSPACE
st.title("🏗️ Engineering Command Center")
tab1, tab2, tab3 = st.tabs(["💬 Engineering Chat", "📊 Cost Dashboard", "🛒 Procurement (PO)"])

# --- TAB 1: CHAT ---
with tab1:
    if "messages" not in st.session_state: st.session_state.messages = []
    
    # A. Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    # B. FLOATING INPUT AREA
    with st.container():
        c1, c2 = st.columns([1, 6])
        with c1:
            audio_data = mic_recorder(
                start_prompt="🎤 Record",
                stop_prompt="⏹️ Stop", 
                key="recorder",
                use_container_width=True
            ) 
        with c2:
            if audio_data and audio_data['bytes']:
                 st.caption("✅ Audio captured. Processing...")
            else:
                 st.caption("Click 'Record' to speak, or type below.")

        if audio_data and audio_data['bytes']:
            if "last_audio_id" not in st.session_state or st.session_state.last_audio_id != audio_data['id']:
                st.session_state.last_audio_id = audio_data['id']
                with st.spinner("🧠 SiteMate is thinking..."):
                    voice_text = transcribe_audio(audio_data['bytes'])
                    if voice_text and "Error" not in voice_text:
                        st.session_state.messages.append({"role": "user", "content": f"🎤 *Voice:* {voice_text}"})
                        # Pass selected_loc instead of hardcoded location
                        ai_resp, boq = get_agent_response(voice_text, selected_loc, soil_type)
                        
                        st.session_state['last_ai_response'] = ai_resp
                        st.session_state['last_user_query'] = voice_text
                        st.markdown(ai_resp)
                        st.session_state.messages.append({"role": "assistant", "content": ai_resp})
                        
                        if boq:
                            st.session_state['active_boq'] = boq
                            st.toast("✅ Project Budget Updated!", icon="💰")
                            time.sleep(1)
                            st.rerun()

    # C. STANDARD TEXT INPUT
    if prompt := st.chat_input("Type your engineering request..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                # Pass selected_loc instead of hardcoded location
                resp_text, boq_data = get_agent_response(prompt, selected_loc, soil_type)
                
                st.session_state['last_ai_response'] = resp_text
                st.session_state['last_user_query'] = prompt
                
                st.markdown(resp_text)
                if boq_data:
                    st.session_state['active_boq'] = boq_data
                    st.success("✅ Dashboard Updated")

        st.session_state.messages.append({"role": "assistant", "content": resp_text})

# --- TAB 2: DASHBOARD (WITH WHAT-IF LOGIC) ---
with tab2:
    col_header, col_btn = st.columns([4,1])
    with col_header:
        if 'active_boq' in st.session_state:
            st.subheader(f"📊 Project Bill of Quantities ({selected_loc})")
            
            # Show active filters
            filters = []
            if steel_var != 0: filters.append(f"Steel {steel_var:+d}%")
            if "M25" in concrete_grade: filters.append("Grade M25")
            
            if filters:
                st.caption(f"⚡ Active Adjustments: {', '.join(filters)}")
            else:
                st.caption("Standard Rates Applied")
        else:
            st.subheader(f"📉 Market Unit Rates ({selected_loc})")

    with col_btn:
        refresh = st.button("🔄 Update Costs", type="primary")

    if refresh or 'active_boq' in st.session_state:
        # Check if we have active BOQ data
        if 'active_boq' in st.session_state:
            target_items = st.session_state['active_boq']
        else:
            target_items = {
                "Cement": 1, "Sharp Sand": 1, "Granite": 1, 
                "12mm Iron Rod": 1, "9-inch Vibrated Block": 1
            }

        live_data = []
        total_act = 0
        
        for item_name, quantity in target_items.items():
            if quantity > 0:
                # Use selected_loc for pricing
                unit_price, full_name = get_live_price(item_name, selected_loc)
                
                # --- APPLY WHAT-IF LOGIC HERE ---
                # 1. Steel Variance
                if "Iron Rod" in item_name or "Steel" in item_name:
                    unit_price = unit_price * (1 + (steel_var / 100.0))
                
                # 2. Concrete Grade
                calc_qty = quantity
                if "Cement" in item_name and "M25" in concrete_grade:
                    calc_qty = quantity * 1.25
                # -------------------------------
                
                line_total = unit_price * calc_qty
                if unit_price == 0: full_name = f"⚠️ {item_name} (Not in DB)"
                
                live_data.append({
                    "Item": item_name, 
                    "Description": full_name, 
                    "Qty": round(calc_qty, 1), 
                    "Unit Price": unit_price, 
                    "Total Cost": line_total
                })
                total_act += line_total

        # SAVE DATAFRAME TO SESSION STATE (CRITICAL FOR PDF)
        if not live_data:
            # Create an empty DataFrame with the correct columns to prevent KeyErrors
            df = pd.DataFrame(columns=["Item", "Description", "Qty", "Unit Price", "Total Cost"])
        else:
            df = pd.DataFrame(live_data)
            
        st.session_state['boq_df'] = df
        st.session_state['total_actual'] = total_act

    if 'boq_df' in st.session_state:
        df = st.session_state['boq_df']
        c1, c2 = st.columns(2)
        c1.metric("Total Project Cost", f"₦{df['Total Cost'].sum():,.0f}")
        c2.metric("Logistics Zone", selected_loc)

        chart = alt.Chart(df).mark_bar().encode(
            x='Item', y='Total Cost', color=alt.value("#FF8C00"), tooltip=['Item', 'Qty', 'Total Cost']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Start a chat in **Tab 1** (Type or Voice) to generate a Bill of Quantities.")

# --- TAB 3: PROCUREMENT (FEATURE 6: WHATSAPP) ---
with tab3:
    st.subheader("🛒 Procurement Orders")
    
    if 'boq_df' in st.session_state:
        df = st.session_state['boq_df']
        valid_orders = df[df['Total Cost'] > 0]
        
        st.markdown(f"**Project Location:** {selected_loc}")
        st.dataframe(valid_orders[['Description', 'Qty', 'Unit Price', 'Total Cost']], use_container_width=True)
        
        # Calculate Grand Total
        grand_total = valid_orders['Total Cost'].sum()
        
        # --- WHATSAPP INTEGRATION ---
        st.divider()
        c1, c2, c3 = st.columns([2, 1, 1])
        
        with c1:
             st.info(f"**Total Payable:** ₦{grand_total:,.0f}")
             
        with c2:
             if st.button("🚀 Process Purchase Orders"):
                 with st.spinner("Generating Invoices..."): time.sleep(2)
                 st.success("Orders sent to suppliers!")
                 st.balloons()
                 
        with c3:
            # Generate WhatsApp Link
            wa_message = f"Hello SiteMate Team,\n\nI want to order materials for the {selected_loc} project.\n\n"
            for _, row in valid_orders.iterrows():
                wa_message += f"- {row['Item']}: {row['Qty']} units\n"
            wa_message += f"\nTotal Estimate: N{grand_total:,.0f}\n\nPlease confirm availability."
            
            encoded_msg = urllib.parse.quote(wa_message)
            wa_link = f"https://wa.me/?text={encoded_msg}"
            
            st.link_button("📲 Share on WhatsApp", wa_link, type="primary")

    else:
        st.warning("⚠️ No active project found. Please chat with SiteMate to create a BOQ.")