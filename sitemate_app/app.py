import streamlit as st
import pandas as pd
import altair as alt
import time

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
    st.caption("v3.1 | Licensed to: **Lekki Projects Ltd**")
    st.divider()
    
    st.subheader("📍 Site Context")
    location = st.selectbox("Project Location", ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"])
    soil_type = st.select_slider("Soil Condition", options=["Firm/Sandy", "Clay", "Swampy"])
    st.divider()

    # --- WHAT-IF SCENARIOS (Feature 4) ---
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
    
    # --- PDF EXPORT (FIXED FOR PRICES) ---
    # Logic: We check for 'boq_df' (The calculated financial table from Tab 2)
    if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
        st.subheader("📄 Export")
        
        pdf_bytes = generate_pdf_report(
            user_query=st.session_state.get('last_user_query', 'N/A'),
            location=location,
            soil_type=soil_type,
            ai_text=st.session_state.get('last_ai_response', ''),
            boq_dataframe=st.session_state['boq_df']  # <--- CRITICAL FIX: Sending the priced dataframe
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
                        ai_resp, boq = get_agent_response(voice_text, location, soil_type)
                        
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
                resp_text, boq_data = get_agent_response(prompt, location, soil_type)
                
                st.session_state['last_ai_response'] = resp_text
                st.session_state['last_user_query'] = prompt
                
                st.markdown(resp_text)
                if boq_data:
                    st.session_state['active_boq'] = boq_data
                    st.success("✅ Dashboard Updated")

        st.session_state.messages.append({"role": "assistant", "content": resp_text})

# --- TAB 2: DASHBOARD (INTERACTIVE) ---
with tab2:
    col_header, col_btn = st.columns([4,1])
    with col_header:
        if 'active_boq' in st.session_state:
            st.subheader(f"📊 Project Bill of Quantities ({location})")
            
            # Show active filters
            filters = []
            if steel_var != 0: filters.append(f"Steel {steel_var:+d}%")
            if "M25" in concrete_grade: filters.append("Grade M25")
            
            if filters:
                st.caption(f"⚡ Active Adjustments: {', '.join(filters)}")
            else:
                st.caption("Standard Rates Applied")
        else:
            st.subheader(f"📉 Market Unit Rates ({location})")

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
                unit_price, full_name = get_live_price(item_name, location)
                
                # --- APPLY WHAT-IF LOGIC HERE ---
                if "Iron Rod" in item_name or "Steel" in item_name:
                    # Apply percentage (+/-)
                    unit_price = unit_price * (1 + (steel_var / 100.0))
                
                calc_qty = quantity
                if "Cement" in item_name and "M25" in concrete_grade:
                    # M25 needs ~25% more cement than M20
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

        # SAVE DATAFRAME TO SESSION STATE
        # This is crucial: We save the *calculated* results so the PDF generator can see them.
        df = pd.DataFrame(live_data)
        st.session_state['boq_df'] = df
        st.session_state['total_actual'] = total_act

    if 'boq_df' in st.session_state:
        df = st.session_state['boq_df']
        c1, c2 = st.columns(2)
        c1.metric("Total Project Cost", f"₦{df['Total Cost'].sum():,.0f}")
        c2.metric("Logistics Zone", location)

        chart = alt.Chart(df).mark_bar().encode(
            x='Item', y='Total Cost', color=alt.value("#FF8C00"), tooltip=['Item', 'Qty', 'Total Cost']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Start a chat in **Tab 1** (Type or Voice) to generate a Bill of Quantities.")

# --- TAB 3: PROCUREMENT ---
with tab3:
    st.subheader("🛒 Procurement Orders")
    
    if 'boq_df' in st.session_state:
        df = st.session_state['boq_df']
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