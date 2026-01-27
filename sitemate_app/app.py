import streamlit as st
import pandas as pd
import altair as alt
import time

# --- 1. IMPORTS ---
from streamlit_mic_recorder import mic_recorder
from logic.transcriber import transcribe_audio
from logic.oyenuga_logic import get_agent_response
from logic.data_fetcher import get_live_price 

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
    st.caption("v3.0 | Licensed to: **Lekki Projects Ltd**")
    st.divider()
    
    st.subheader("📍 Site Context")
    location = st.selectbox("Project Location", ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"])
    soil_type = st.select_slider("Soil Condition", options=["Firm/Sandy", "Clay", "Swampy"])
    st.divider()
    
    # LIVE BUDGET METRIC
    if 'total_actual' in st.session_state:
        val = st.session_state['total_actual']
        st.metric(label="Live Project Budget", value=f"₦ {val:,.0f}", delta="Synced with Chat")
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
    # We create a container to hold Voice + Text controls cleanly
    with st.container():
        # Layout: Microphone on the left, Status text on the right
        c1, c2 = st.columns([1, 6])
        
        with c1:
            # Minimalist Mic Button
            audio_data = mic_recorder(
                start_prompt="🎤 Record",
                stop_prompt="⏹️ Stop", 
                key="recorder",
                use_container_width=True
            )
            
        with c2:
            # Placeholder to show we are listening
            if audio_data and audio_data['bytes']:
                 st.caption("✅ Audio captured. Processing...")
            else:
                 st.caption("Click 'Record' to speak, or type below.")

        # Logic: Process Voice
        if audio_data and audio_data['bytes']:
            # Prevent re-processing the same audio twice
            if "last_audio_id" not in st.session_state or st.session_state.last_audio_id != audio_data['id']:
                st.session_state.last_audio_id = audio_data['id']
                
                with st.spinner("🧠 SiteMate is thinking..."):
                    voice_text = transcribe_audio(audio_data['bytes'])
                    
                    if voice_text and "Error" not in voice_text:
                        # Add User Voice to Chat
                        st.session_state.messages.append({"role": "user", "content": f"🎤 *Voice:* {voice_text}"})
                        
                        # Get AI Response (Now checks for "Cancel"!)
                        ai_resp, boq = get_agent_response(voice_text, location, soil_type)
                        
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
                st.markdown(resp_text)
                
                if boq_data:
                    st.session_state['active_boq'] = boq_data
                    st.success("✅ Dashboard Updated")

        st.session_state.messages.append({"role": "assistant", "content": resp_text})

# --- TAB 2: DASHBOARD ---
with tab2:
    col_header, col_btn = st.columns([4,1])
    with col_header:
        if 'active_boq' in st.session_state:
            st.subheader(f"📊 Project Bill of Quantities ({location})")
        else:
            st.subheader(f"📉 Market Unit Rates ({location})")

    with col_btn:
        refresh = st.button("🔄 Update Costs", type="primary")

    if refresh or 'active_boq' in st.session_state:
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
                line_total = unit_price * quantity
                if unit_price == 0: full_name = f"⚠️ {item_name} (Not in DB)"
                
                live_data.append({
                    "Item": item_name, "Description": full_name, "Qty": quantity,
                    "Unit Price": unit_price, "Total Cost": line_total
                })
                total_act += line_total

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