import streamlit as st
import pandas as pd
import altair as alt
import time

# --- 1. IMPORTS ---
from streamlit_mic_recorder import mic_recorder
from logic.transcriber import transcribe_audio
from logic.oyenuga_logic import get_agent_response
from logic.data_fetcher import get_live_price, get_suppliers_for_location
from logic.report_generator import generate_pdf_report
from logic.integrations import get_whatsapp_link, get_email_link, generate_order_message
from logic.labor_engine import calculate_labor_cost
from logic.timeline_engine import calculate_project_timeline
from logic.db_manager import init_db, save_project, get_all_projects, load_project_data, delete_project
from logic.weather_engine import get_site_weather
from logic.expert_verifier import verify_project_budget 

# 2. PAGE CONFIG & DB INIT
st.set_page_config(page_title="SiteMate Pro", page_icon="🏗️", layout="wide")
try:
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except:
    pass 

init_db()

# 3. SIDEBAR
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=60)
    st.title("SiteMate Pro")
    st.caption("v12.2 (Complete) | Licensed to: **Lekki Projects Ltd**")
    st.divider()
    
    # --- FEATURE: PROJECT HISTORY ---
    with st.expander("🗂️ My Projects", expanded=False):
        save_name = st.text_input("Project Name", placeholder="e.g. Lekki Fence")
        if st.button("💾 Save Project"):
            if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
                loc_to_save = st.session_state.get('last_location', "Lekki, Lagos")
                soil_to_save = st.session_state.get('soil_default', "Firm/Sandy")
                success, msg = save_project(save_name, loc_to_save, soil_to_save, st.session_state['boq_df'])
                if success:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun() 
                else:
                    st.error(msg)
            else:
                st.warning("No active project data to save.")

        st.divider()

        existing_projects = get_all_projects() 
        if existing_projects:
            project_names = [p[0] for p in existing_projects]
            selected_load = st.selectbox("Select Project", project_names)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📂 Load"):
                    loc, soil, df = load_project_data(selected_load)
                    if df is not None:
                        st.session_state['boq_df'] = df
                        st.session_state['last_location'] = loc
                        st.session_state['soil_default'] = soil
                        st.session_state['active_boq'] = True 
                        st.success(f"Loaded: {selected_load}")
                        time.sleep(1)
                        st.rerun()
            with c2:
                if st.button("❌ Delete"):
                    delete_project(selected_load)
                    st.warning("Deleted.")
                    time.sleep(1)
                    st.rerun()
        else:
            st.caption("No saved projects yet.")

    st.divider()
    
    # --- FEATURE: SMART GEOLOCATION & WEATHER ---
    st.subheader("📍 Site Context")
    SOIL_DEFAULTS = {"Lekki, Lagos": "Swampy", "Ibadan, Oyo": "Firm/Sandy", "Abuja, FCT": "Firm/Sandy"}
    
    if "last_location" not in st.session_state: st.session_state.last_location = "Lekki, Lagos"
    selected_loc = st.selectbox("Project Location", ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"], index=["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"].index(st.session_state.last_location), key="loc_selector")
    
    if selected_loc != st.session_state.last_location:
        st.session_state.last_location = selected_loc
        st.session_state.soil_default = SOIL_DEFAULTS[selected_loc]

    # Weather Widget
    weather_data = get_site_weather(selected_loc)
    if weather_data and "error" not in weather_data:
        st.markdown(f"""
        <div style="background-color: #f0f2f6; color: #333333; padding: 10px; border-radius: 8px; border-left: 4px solid #3498db;">
            <b>🌤️ Site Weather:</b> {weather_data['temp']}°C | {weather_data['condition']}
        </div>
        """, unsafe_allow_html=True)
        if not weather_data.get('is_safe', True):
            st.error(weather_data['advice'])
        elif weather_data['temp'] > 32:
            st.warning(weather_data['advice'])

    soil_type = st.select_slider("Soil Condition", options=["Firm/Sandy", "Clay", "Swampy"], value=st.session_state.get("soil_default", "Firm/Sandy"))
    if soil_type == SOIL_DEFAULTS[selected_loc]: st.caption(f"✨ *Auto-detected soil for {selected_loc.split(',')[0]}*")
    st.divider()

    # --- FEATURE: WHAT-IF SCENARIOS ---
    with st.expander("⚡ What-If Scenarios", expanded=False):
        st.caption("Adjust parameters to see instant cost impact.")
        steel_var = st.slider("📉 Steel Price Variance", -10, 20, 0, format="%d%%")
        concrete_grade = st.radio("🏗️ Concrete Grade", ["M20 (Standard)", "M25 (Heavy Duty)"])
        if concrete_grade == "M25 (Heavy Duty)": st.caption("ℹ️ *M25 requires ~25% more cement.*")
        if steel_var != 0: st.caption(f"ℹ️ *Steel adjusted by {steel_var}%.*")
    st.divider()
    
    # --- FEATURE: EXPORT (Bank Format) ---
    if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
        st.subheader("📄 Report Type")
        report_choice = st.radio("Format:", ["Standard Estimate", "Bank Loan Valuation"])
        
        # Map choice to backend type
        rpt_type = "Bank" if report_choice == "Bank Loan Valuation" else "Standard"
        
        pdf_bytes = generate_pdf_report(
            user_query=st.session_state.get('last_user_query', 'N/A'),
            location=selected_loc,
            soil_type=soil_type,
            ai_text=st.session_state.get('last_ai_response', ''),
            boq_dataframe=st.session_state['boq_df'],
            report_type=rpt_type
        )
        st.download_button("📥 Download Report", data=pdf_bytes, file_name=f"SiteMate_{rpt_type}_Report.pdf", mime="application/pdf", type="primary", use_container_width=True)
        st.divider()

    # LIVE METRIC
    if 'total_project_cost' in st.session_state:
        st.metric(label="Total Project Budget", value=f"₦ {st.session_state['total_project_cost']:,.0f}", delta="Materials + Labor")
    else:
        st.metric(label="Live Project Budget", value="--")

# 4. MAIN WORKSPACE
st.title("🏗️ Engineering Command Center")
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Dashboard", "🛒 Marketplace"])

# --- TAB 1: CHAT ---
with tab1:
    if "messages" not in st.session_state: st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    with st.container():
        c1, c2 = st.columns([1, 6])
        with c1: audio_data = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹️ Stop", key="recorder", use_container_width=True) 
        with c2: st.caption("Click 'Record' to speak, or type below.")

        if audio_data and audio_data['bytes']:
            if "last_audio_id" not in st.session_state or st.session_state.last_audio_id != audio_data['id']:
                st.session_state.last_audio_id = audio_data['id']
                with st.spinner("🧠 SiteMate is thinking..."):
                    voice_text = transcribe_audio(audio_data['bytes'])
                    if voice_text and "Error" not in voice_text:
                        st.session_state.messages.append({"role": "user", "content": f"🎤 *Voice:* {voice_text}"})
                        ai_resp, boq = get_agent_response(voice_text, selected_loc, soil_type)
                        st.session_state['last_ai_response'] = ai_resp
                        st.session_state['last_user_query'] = voice_text
                        st.session_state.messages.append({"role": "assistant", "content": ai_resp})
                        st.markdown(ai_resp)
                        if boq:
                            st.session_state['active_boq'] = boq
                            st.toast("✅ Project Budget Updated!", icon="💰")
                            time.sleep(1)
                            st.rerun()

    if prompt := st.chat_input("Type your engineering request..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                resp_text, boq_data = get_agent_response(prompt, selected_loc, soil_type)
                st.session_state['last_ai_response'] = resp_text
                st.session_state['last_user_query'] = prompt
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
            st.subheader(f"📊 Project Analytics ({selected_loc})")
            filters = []
            if steel_var != 0: filters.append(f"Steel {steel_var:+d}%")
            if "M25" in concrete_grade: filters.append("Grade M25")
            if filters: st.caption(f"⚡ Active Adjustments: {', '.join(filters)}")
        else:
            st.subheader(f"📉 Market Unit Rates ({selected_loc})")

    with col_btn:
        refresh = st.button("🔄 Update", type="primary")
        
    # --- EXPERT WITNESS VERIFICATION ---
    if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
        with st.expander("🛡️ Expert Verification Service", expanded=False):
            st.info("Have a Senior QS Audit your budget before sending to a bank.")
            if st.button("🔍 Verify My Budget"):
                with st.spinner("Consulting Senior Engineer AI..."):
                    audit_report = verify_project_budget(st.session_state['boq_df'], selected_loc)
                    st.markdown(audit_report)

    if refresh or 'active_boq' in st.session_state:
        if isinstance(st.session_state.get('active_boq'), dict):
            target_items = st.session_state['active_boq']
            live_data = []
            material_total = 0
            for item_name, quantity in target_items.items():
                if quantity > 0:
                    unit_price, full_name = get_live_price(item_name, selected_loc)
                    
                    # Apply What-If Adjustments
                    if "Iron Rod" in item_name or "Steel" in item_name: 
                        unit_price *= (1 + (steel_var / 100.0))
                    
                    calc_qty = quantity * 1.25 if "Cement" in item_name and "M25" in concrete_grade else quantity
                    
                    line_total = unit_price * calc_qty
                    if unit_price == 0: full_name = f"⚠️ {item_name} (Not in DB)"
                    
                    live_data.append({"Item": item_name, "Description": full_name, "Qty": round(calc_qty, 1), "Unit Price": unit_price, "Total Cost": line_total})
                    material_total += line_total
            st.session_state['boq_df'] = pd.DataFrame(live_data) if live_data else pd.DataFrame(columns=["Item", "Description", "Qty", "Unit Price", "Total Cost"])
        
        if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
            mat_df = st.session_state['boq_df']
            labor_df = calculate_labor_cost(mat_df)
            timeline_df = calculate_project_timeline(mat_df)
            st.session_state['labor_df'] = labor_df
            st.session_state['timeline_df'] = timeline_df
            st.session_state['total_project_cost'] = mat_df['Total Cost'].sum() + (labor_df['Amount'].sum() if not labor_df.empty else 0)

    if 'boq_df' in st.session_state:
        mat_df = st.session_state['boq_df']
        m1, m2, m3 = st.columns(3)
        m1.metric("🧱 Material Cost", f"₦{mat_df['Total Cost'].sum():,.0f}")
        labor_val = st.session_state.get('labor_df', pd.DataFrame())['Amount'].sum() if 'labor_df' in st.session_state else 0
        m2.metric("👷 Labor", f"₦{labor_val:,.0f}")
        m3.metric("💰 Grand Total", f"₦{mat_df['Total Cost'].sum() + labor_val:,.0f}")
        st.divider()

        tab_mat, tab_lab, tab_time = st.tabs(["Materials", "Labor", "Schedule"])
        with tab_mat:
            st.dataframe(mat_df, use_container_width=True, hide_index=True)
        with tab_lab:
            st.dataframe(st.session_state.get('labor_df'), use_container_width=True, hide_index=True)
        
        # --- RESTORED GANTT CHART ---
        with tab_time:
            if 'timeline_df' in st.session_state and not st.session_state['timeline_df'].empty:
                t_df = st.session_state['timeline_df']
                # Create the Gantt Chart using Altair
                gantt = alt.Chart(t_df).mark_bar().encode(
                    x='Start', 
                    x2='End', 
                    y=alt.Y('Phase', sort=None), 
                    color=alt.value("#3498db"),
                    tooltip=['Phase', 'Start', 'End', 'Duration']
                ).properties(height=300)
                
                st.altair_chart(gantt, use_container_width=True)
                st.dataframe(t_df, use_container_width=True, hide_index=True)
            else:
                st.info("Timeline requires material data.")

# --- TAB 3: PROCUREMENT ---
with tab3:
    st.subheader(f"🛒 Suppliers in {selected_loc}")
    if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
        df = st.session_state['boq_df']
        base_total = df['Total Cost'].sum()
        suppliers = get_suppliers_for_location(selected_loc)
        for supplier in suppliers:
            supplier_total = base_total * supplier.get('markup', 1.0)
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 2])
                with c1:
                    st.markdown(f"### 🏭 {supplier['name']}")
                    st.caption(f"Rating: {supplier['rating']}")
                    st.markdown(f"**Total Quote:** ₦{supplier_total:,.0f}")
                with c2:
                    order_msg = generate_order_message(selected_loc, df, supplier['name'])
                    wa_link = get_whatsapp_link(supplier['phone'], order_msg)
                    if wa_link: st.link_button("📲 WhatsApp", wa_link)
                with c3:
                    email_link = get_email_link(supplier['email'], selected_loc, order_msg)
                    if email_link: st.markdown(f"""<a href="{email_link}" target="_blank" style="text-decoration:none;"><button style="width:100%; padding: 0.5rem; background-color: #f0f2f6; border: 1px solid #ccc; border-radius: 5px; cursor: pointer;">📧 Email</button></a>""", unsafe_allow_html=True)
    else:
        st.warning("Create a BOQ to view suppliers.")