import streamlit as st
import pandas as pd
import altair as alt
import time
import os

# --- 0. THEME AUTO-FIX (FORCES DARK MODE) ---
# This ensures the app ALWAYS loads in Dark Mode on the Cloud.
if not os.path.exists(".streamlit/config.toml"):
    os.makedirs(".streamlit", exist_ok=True)
    with open(".streamlit/config.toml", "w") as f:
        f.write("""
[theme]
base="dark"
primaryColor="#FF8C00"
backgroundColor="#0E1117"
secondaryBackgroundColor="#161B22"
textColor="#E6EDF3"
font="sans serif"
""")

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="SiteMate Pro", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

# --- 2. IMPORTS ---
from streamlit_mic_recorder import mic_recorder
from logic.transcriber import transcribe_audio
from logic.oyenuga_logic import get_agent_response
from logic.data_fetcher import get_live_price, get_suppliers_for_location
from logic.report_generator import generate_pdf_report, generate_diary_pdf, generate_inventory_pdf, generate_expense_pdf
from logic.integrations import get_whatsapp_link, get_email_link
from logic.labor_engine import calculate_labor_cost
from logic.timeline_engine import calculate_project_timeline
from logic.db_manager import (
    init_db, save_project, get_all_projects, load_project_data, delete_project, 
    get_bids_for_project, register_supplier, get_open_tenders, submit_bid,
    log_expense, get_project_expenses, update_inventory, get_project_inventory, 
    get_inventory_logs, log_site_diary, get_site_diary, 
    get_all_supplier_names, update_bid_status, get_supplier_bids
)
from logic.weather_engine import get_site_weather
from logic.expert_verifier import verify_project_budget 
from logic.feasibility_engine import check_feasibility 
from logic.auth import require_auth, logout 

# --- 3. CUSTOM STYLING (THE AGGRESSIVE FIX) ---
CUSTOM_CSS = """
/* --- GLOBAL THEME --- */
:root {
    --primary-color: #FF8C00; 
    --bg-dark: #0E1117; 
    --bg-card: #161B22; 
    --text-white: #FFFFFF;
}

/* 1. FORCE BACKGROUNDS */
.stApp { background-color: var(--bg-dark); }
[data-testid="stSidebar"] { background-color: var(--bg-card); border-right: 1px solid #30363D; }

/* 2. FORCE TEXT COLORS (Global White) */
h1, h2, h3, h4, h5, h6, p, label, span, div { color: var(--text-white) !important; }

/* 3. SIDEBAR NAVIGATION BUTTONS (Aggressive Override) */
[data-testid="stRadio"] > div { gap: 10px; }
[data-testid="stRadio"] label {
    background-color: #0d1117 !important;
    color: #FFFFFF !important; /* Force White Text */
    border: 1px solid #30363D !important;
    padding: 12px !important;
    border-radius: 8px !important;
}
/* Hover State */
[data-testid="stRadio"] label:hover {
    border-color: #FF8C00 !important;
    cursor: pointer;
}
/* Selected State */
[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {
    background-color: #FF8C00 !important;
    border-color: #FF8C00 !important;
}
/* Selected Text Color (Black for contrast on Orange) */
[data-testid="stRadio"] label[data-baseweb="radio"] p {
    color: #000000 !important;
    font-weight: 800 !important;
}

/* 4. FIX WHITE BOXES (Selectbox & Inputs) */
/* This targets the internal React component to force dark mode */
div[data-baseweb="select"] > div, 
div[data-baseweb="input"] > div {
    background-color: #1F242C !important;
    color: white !important;
    border-color: #30363D !important;
}
/* Fix the dropdown popover menu */
div[data-baseweb="popover"], div[data-baseweb="menu"] {
    background-color: #161B22 !important;
}
/* Ensure text inside selectbox is white */
div[data-baseweb="select"] span {
    color: white !important;
}
/* Ensure placeholder text is visible */
input::placeholder {
    color: #B0B8C4 !important;
}
input {
    color: white !important;
}

/* 5. USER CARD & WIDGETS */
.user-card {
    background: linear-gradient(135deg, #1f2937, #111827);
    border: 1px solid #374151;
    border-left: 5px solid #FF8C00;
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
}
.context-card {
    background-color: #21262d;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #30363d;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* 6. BUTTONS */
button[kind="primary"] {
    background-color: #FF8C00 !important;
    color: white !important;
    border: none;
    font-weight: bold;
}
button[kind="secondary"] {
    background-color: #21262D !important;
    color: white !important;
    border: 1px solid #30363D !important;
}

/* 7. HIDE BRANDING */
#MainMenu, footer, header {visibility: hidden;}
"""
st.markdown(f'<style>{CUSTOM_CSS}</style>', unsafe_allow_html=True)

init_db()

# --- 4. AUTHENTICATION ---
require_auth()

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.markdown("### **SiteMate Pro**")
    st.caption("Enterprise OS | v1.0")
    
    # --- USER CARD ---
    st.markdown(f"""
    <div class="user-card">
        <small style="color: #9ca3af;">Logged in as:</small><br>
        <strong style="font-size: 1.1em;">{st.session_state['user_name']}</strong><br>
        <div style="margin-top: 5px;">
            <span style='color: #4ade80; font-size: 0.8em;'>● Online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- CONTEXT SECTION ---
    st.markdown("#### 📍 Context")
    if "last_location" not in st.session_state: st.session_state.last_location = "Lekki, Lagos"
    selected_loc = st.selectbox("Location", ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"], index=["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"].index(st.session_state.last_location))
    
    if selected_loc != st.session_state.last_location:
        st.session_state.last_location = selected_loc
        st.rerun()

    # --- WEATHER WIDGET ---
    weather_data = get_site_weather(selected_loc)
    if weather_data and "error" not in weather_data:
        st.markdown(f"""
        <div class="context-card">
            <span style="font-size: 1.5em;">🌤️</span>
            <div>
                <b>{weather_data['temp']}°C</b><br>
                <span style="color: #8b949e;">{weather_data['condition']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # NAVIGATION MENU
    available_tabs = []
    if "plan" in st.session_state.permissions: available_tabs.append("📐 Planning & AI")
    if "bid" in st.session_state.permissions: available_tabs.append("🛒 Marketplace")
    if "supply" in st.session_state.permissions: available_tabs.append("🚚 Supplier Portal")
    if "site" in st.session_state.permissions: available_tabs.append("🚧 Site Operations")
    
    selected_nav = st.radio("Go to:", available_tabs, label_visibility="collapsed")
    
    st.divider()
    if st.button("🚪 Sign Out"): logout()

# --- 6. MAIN CONTENT AREA ---

# ==========================================
# 📐 TAB 1: PLANNING & AI
# ==========================================
if selected_nav == "📐 Planning & AI":
    st.title("📐 Engineering Command Center")
    st.caption(f"Project Planning & Estimation for **{selected_loc}**")
    
    p_tab1, p_tab2, p_tab3 = st.tabs(["💬 AI Architect", "⚡ Analysis & Scenarios", "📄 Reports & Exports"])
    
    with p_tab1:
        # Chat Interface
        if "messages" not in st.session_state: st.session_state.messages = []
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
        # Audio Input
        c1, c2 = st.columns([1, 6])
        with c1: audio_data = mic_recorder(start_prompt="🎤 Record", stop_prompt="⏹️ Stop", key="recorder", use_container_width=True)
        
        if audio_data and audio_data['bytes']:
             if "last_audio_id" not in st.session_state or st.session_state.get('last_audio_id') != audio_data['id']:
                st.session_state.last_audio_id = audio_data['id']
                with st.spinner("Transcribing..."):
                    text = transcribe_audio(audio_data['bytes'])
                    if text: 
                        st.session_state.messages.append({"role": "user", "content": f"🎤 {text}"})
                        soil = "Swampy" if "Lekki" in selected_loc else "Firm"
                        resp, boq = get_agent_response(text, selected_loc, soil)
                        st.session_state.messages.append({"role": "assistant", "content": resp})
                        if boq:
                             st.session_state['active_boq'] = boq
                             st.session_state['boq_df'] = pd.DataFrame([{"Item": k, "Qty": v, "Unit Price": get_live_price(k, selected_loc)[0], "Total Cost": v * get_live_price(k, selected_loc)[0]} for k, v in boq.items()])
                        st.rerun()

        if prompt := st.chat_input("Ask SiteMate..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Calculating..."):
                    soil = "Swampy" if "Lekki" in selected_loc else "Firm"
                    resp, boq = get_agent_response(prompt, selected_loc, soil)
                    st.markdown(resp)
                    st.session_state.messages.append({"role": "assistant", "content": resp})
                    
                    if boq:
                        st.session_state['active_boq'] = boq
                        st.session_state['boq_df'] = pd.DataFrame([{"Item": k, "Qty": v, "Unit Price": get_live_price(k, selected_loc)[0], "Total Cost": v * get_live_price(k, selected_loc)[0]} for k, v in boq.items()])
                        st.success("✅ BOQ Generated")

        # Save Logic
        if 'active_boq' in st.session_state:
            with st.expander("💾 Save This Project to Cloud", expanded=True):
                c1, c2 = st.columns([3, 1])
                with c1: save_name = st.text_input("Project Name", placeholder="e.g. Lekki Bungalow Phase 1")
                with c2: 
                    if st.button("Save Project", type="primary", use_container_width=True):
                        soil_to_save = st.session_state.get('soil_default', "Firm")
                        success, msg = save_project(save_name, selected_loc, soil_to_save, st.session_state['boq_df'])
                        if success:
                            st.session_state['current_project_name'] = save_name
                            st.success("Saved & Synced to Algolia!")
                        else: st.error(msg)

    # --- TAB 2: ANALYSIS & SCENARIOS ---
    with p_tab2:
        st.subheader("⚡ Risk Analysis & Scenarios")
        
        if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
            
            # 1. WHAT-IF SCENARIOS
            c1, c2 = st.columns(2)
            with c1: 
                steel_var = st.slider("📉 Steel Price Variance", -10, 20, 0, format="%d%%")
            with c2: 
                concrete_grade = st.radio("🏗️ Concrete Grade", ["M20 (Standard)", "M25 (Heavy Duty)"], horizontal=True)

            if st.button("🔄 Recalculate Budget"):
                target_items = st.session_state['active_boq']
                live_data = []
                for item_name, quantity in target_items.items():
                    if quantity > 0:
                        unit_price, full_name = get_live_price(item_name, selected_loc)
                        if "Iron Rod" in item_name or "Steel" in item_name: unit_price *= (1 + (steel_var / 100.0))
                        calc_qty = quantity * 1.25 if "Cement" in item_name and "M25" in concrete_grade else quantity
                        live_data.append({"Item": item_name, "Qty": round(calc_qty, 1), "Unit Price": unit_price, "Total Cost": unit_price * calc_qty})
                
                st.session_state['boq_df'] = pd.DataFrame(live_data)
                st.success("Budget Recalculated!")
            
            st.dataframe(st.session_state['boq_df'], use_container_width=True)
            st.metric("New Grand Total", f"₦{st.session_state['boq_df']['Total Cost'].sum():,.0f}")
            
            st.divider()

            # 2. GANTT CHART
            st.subheader("📅 Estimated Project Schedule")
            try:
                timeline_df = calculate_project_timeline(st.session_state['boq_df'])
                if not timeline_df.empty:
                    chart = alt.Chart(timeline_df).mark_bar().encode(
                        x=alt.X('Start', title='Start Date'),
                        x2='End',
                        y=alt.Y('Task', sort=None, title='Construction Phase'),
                        color=alt.Color('Phase', legend=alt.Legend(title="Phase Type")),
                        tooltip=['Task', 'Start', 'End', 'Duration (Days)']
                    ).properties(height=300)
                    st.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.info("Timeline generation pending project details.")

            st.divider()

            # 3. EXPERT VERIFICATION
            with st.expander("🛡️ Expert Verification Service (Senior QS)", expanded=False):
                st.info("Have a Senior QS AI audit your budget before sending it to a bank.")
                if st.button("🔍 Verify My Budget"):
                    with st.spinner("Consulting Senior Engineer AI..."):
                        audit_report = verify_project_budget(st.session_state['boq_df'], selected_loc)
                        st.markdown(audit_report)
        else:
            st.info("Generate a BOQ in the Chat tab first.")

    # --- REPORTS & PROJECT MANAGEMENT ---
    with p_tab3:
        st.subheader("📂 Project Management & Reports")
        
        # 1. PROJECT LOADER
        projects = get_all_projects()
        if projects:
            proj_list = [p[0] for p in projects]
            
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                sel_proj = st.selectbox("Select Project", proj_list, label_visibility="collapsed")
            with c2:
                if st.button("📂 Load"):
                    loc, soil, df = load_project_data(sel_proj)
                    if df is not None:
                        st.session_state['boq_df'] = df
                        st.session_state['current_project_name'] = sel_proj
                        st.success(f"Loaded {sel_proj}")
                        time.sleep(1)
                        st.rerun()
            with c3:
                if st.button("❌ Delete", type="primary"):
                    delete_project(sel_proj)
                    if st.session_state.get('current_project_name') == sel_proj:
                        st.session_state['current_project_name'] = None
                        st.session_state['boq_df'] = pd.DataFrame()
                    st.toast(f"Deleted {sel_proj}")
                    time.sleep(1)
                    st.rerun()
        else:
            st.info("No saved projects found.")

        st.divider()

        # 2. REPORT GENERATION
        st.subheader("🖨️ Generate PDF Reports")
        if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
            report_choice = st.radio("Select Format:", ["Standard Estimate", "Bank Loan Valuation (Financier Ready)"])
            
            rpt_type = "Bank" if "Bank" in report_choice else "Standard"
            
            pdf_bytes = generate_pdf_report(
                user_query="Project Estimation",
                location=selected_loc,
                soil_type="Standard",
                ai_text="Generated via SiteMate Pro",
                boq_dataframe=st.session_state['boq_df'],
                report_type=rpt_type
            )
            
            st.download_button(
                label=f"📥 Download {rpt_type} PDF", 
                data=pdf_bytes, 
                file_name=f"SiteMate_{rpt_type}_Report.pdf", 
                mime="application/pdf", 
                type="primary", 
                use_container_width=True
            )
        else:
            st.caption("Load a project above or create a new one in 'AI Architect' to generate reports.")

# ==========================================
# 🛒 TAB 2: MARKETPLACE (The "Admin" View)
# ==========================================
elif selected_nav == "🛒 Marketplace":
    st.title("🛒 Procurement Marketplace")
    current_proj = st.session_state.get('current_project_name')
    if not current_proj:
        st.warning("⚠️ No Project Selected. Please go to 'Planning' and Load/Save a project first.")
    else:
        st.info(f"Viewing Bids for: **{current_proj}**")
        _, _, proj_df = load_project_data(current_proj)
        est_total = proj_df['Total Cost'].sum() if proj_df is not None else 0
        bids = get_bids_for_project(current_proj)
        
        # --- SECTION 1: LIVE BIDS ---
        st.markdown("### 🔔 Active Bids")
        if not bids: 
            st.info("Waiting for suppliers to bid...")
        else:
            for bid in bids:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.markdown(f"### 🏭 {bid['supplier_name']}")
                        if est_total > 0:
                            diff = ((bid['amount'] - est_total) / est_total) * 100
                            if abs(diff) <= 10: st.success(f"✅ Fair Price (Within {diff:.1f}% of AI Estimate)")
                            elif diff > 10: st.warning(f"⚠️ High Bid (+{diff:.1f}%)")
                            else: st.warning(f"📉 Suspiciously Low ({diff:.1f}%)")
                    with c2:
                        st.metric("Bid Amount", f"₦{bid['amount']:,.0f}")
                        st.caption(f"Status: **{bid['status']}**")
                    with c3:
                         if bid['status'] == 'Pending':
                             if st.button("✅ Accept", key=f"acc_{bid['id']}"):
                                 update_bid_status(bid['id'], "Accepted")
                                 st.rerun()
                             if st.button("❌ Reject", key=f"rej_{bid['id']}"):
                                 update_bid_status(bid['id'], "Rejected")
                                 st.rerun()
                         elif bid['status'] == 'Accepted':
                             st.success("Accepted!")
                             st.link_button("💳 Pay Now", "https://paystack.com", help="Payment Gateway")
                         elif bid['status'] == 'Rejected':
                             st.error("Rejected")

        st.divider()

        # --- SECTION 2: STANDARD SUPPLIERS ---
        st.markdown("### 📚 Standard Suppliers Directory")
        st.caption("Contact registered suppliers directly if you don't want to wait for bids.")
        
        if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
            base_total = st.session_state['boq_df']['Total Cost'].sum()
            suppliers = get_suppliers_for_location(selected_loc)
            
            if not suppliers:
                st.warning("No suppliers registered in this location yet.")
            else:
                for sup in suppliers:
                    supplier_total = base_total * sup.get('markup', 1.05)
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 2])
                        with c1:
                            st.markdown(f"**{sup['name']}**")
                            st.caption(f"⭐ {sup.get('rating', 'New')} | 📍 {selected_loc}")
                            st.write(f"**Est. Quote:** ₦{supplier_total:,.0f}")
                        with c2:
                            st.link_button("📲 Chat", get_whatsapp_link(sup.get('phone', '000'), "Hello, I have a project..."))
                        with c3:
                            email_link = get_email_link(sup.get('email', 'test@test.com'), selected_loc, "Order Inquiry")
                            if email_link: 
                                st.link_button("📧 Send Email", email_link, use_container_width=True)
        else:
            st.info("Create a BOQ in the Planning tab to see supplier estimates.")

# ==========================================
# 🚚 TAB 3: SUPPLIER PORTAL (The "Vendor" View)
# ==========================================
elif selected_nav == "🚚 Supplier Portal":
    st.title("🚚 Supplier Portal")
    
    active_user = st.session_state['user_name']
    
    if st.session_state.get('role') == "Chief Engineer":
        st.info("👮 **Admin Mode:** You are impersonating a supplier.")
        registered_suppliers = get_all_supplier_names()
        active_user = st.selectbox("Simulate As:", registered_suppliers)
    
    s_tab1, s_tab2, s_tab3 = st.tabs(["💰 Job Board", "📂 My Bids (Status)", "📝 New Registration"])
    
    with s_tab1:
        st.markdown(f"### 🔍 Live Tenders (Viewing as: {active_user})")
        tenders = get_open_tenders(selected_loc)
        
        if not tenders:
            st.info(f"No active tenders found in {selected_loc}.")
        else:
            for job in tenders:
                with st.expander(f"📢 {job['name']} ({job['items']} Items Needed)"):
                    st.write(f"**Est. Value:** ₦{job['est_value']:,.0f}")
                    c1, c2 = st.columns([2,1])
                    with c1: bid_amt = st.number_input("Your Bid (₦)", min_value=100000.0, step=10000.0, key=f"bid_{job['name']}")
                    with c2:
                        st.write("") 
                        if st.button("🚀 Submit Bid", key=f"sub_{job['name']}"):
                            if submit_bid(job['name'], active_user, bid_amt, "08012345678"):
                                st.success(f"Bid Sent as '{active_user}'!")
                            else: st.error("Error submitting bid.")

    with s_tab2:
        st.markdown(f"### 📂 Bid History for {active_user}")
        my_bids = get_supplier_bids(active_user)
        
        if not my_bids:
            st.info("You haven't submitted any bids yet.")
        else:
            for bid in my_bids:
                status = bid['status'] 
                color = "orange" if status == "Pending" else "green" if status == "Accepted" else "red"
                
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**Project:** {bid['project_name']}")
                        st.caption(f"Bid Amount: ₦{bid['amount']:,.0f} | Date: {bid['timestamp']}")
                    with c2:
                        st.markdown(f":{color}[**{status}**]")

    with s_tab3:
        st.markdown("### 📝 Register Business")
        with st.form("reg_form"):
            r_name = st.text_input("Company Name")
            r_loc = st.selectbox("Base Location", ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"])
            r_phone = st.text_input("WhatsApp Number")
            r_email = st.text_input("Email Address")
            r_items = st.multiselect("Supply Items", ["Cement", "Sharp Sand", "Granite", "Iron Rods", "Blocks"])
            
            if st.form_submit_button("✅ Register"):
                if register_supplier(r_name, r_loc, r_phone, r_email, r_items):
                    st.success(f"Registered {r_name}!")
                    st.rerun()

# ==========================================
# 🚧 TAB 4: SITE OPERATIONS (The "Site Manager" View)
# ==========================================
elif selected_nav == "🚧 Site Operations":
    st.title("🚧 Site Execution Manager")
    
    logger_name = "Site Manager"
    if st.session_state.get('role') == "Chief Engineer":
        st.info("👮 **Admin Mode:** Logging site data as 'Site Manager Tunde'.")
        logger_name = "Site Manager Tunde"

    current_proj = st.session_state.get('current_project_name')
    if not current_proj: 
        st.error("Please load a project in the 'Planning' tab first.")
    else:
        st.success(f"Managing Site: **{current_proj}**")
        
        df_exp = get_project_expenses(current_proj)
        inventory_df = get_project_inventory(current_proj)
        history_df = get_inventory_logs(current_proj)
        diary_df = get_site_diary(current_proj)

        op_tab1, op_tab2, op_tab3 = st.tabs(["💸 Expense Log", "📦 Inventory Control", "📅 Daily Diary (DSR)"])
        
        with op_tab1:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("#### Log Expense")
                with st.form("exp_form"):
                    e_item = st.text_input("Item", placeholder="e.g. Diesel")
                    e_amt = st.number_input("Amount (₦)", min_value=0.0, step=1000.0)
                    e_cat = st.selectbox("Category", ["Materials", "Labor", "Logistics", "Permits", "Misc"])
                    e_note = st.text_input("Note", placeholder="Receipt #...")
                    
                    if st.form_submit_button("💾 Save Expense"):
                        log_expense(current_proj, e_item, e_amt, e_cat, f"{e_note} (By {logger_name})")
                        st.success("Saved to Ledger")
                        st.rerun()
            
            with c2:
                st.markdown("#### Financial Overview")
                if not df_exp.empty:
                    st.dataframe(df_exp, use_container_width=True)
                    st.metric("Total Spent", f"₦{df_exp['amount'].sum():,.0f}")
                    pdf_bytes = generate_expense_pdf(current_proj, 0, df_exp)
                    st.download_button("📥 Download Ledger PDF", pdf_bytes, "expense_log.pdf", "application/pdf")
                else:
                    st.info("No expenses logged yet.")

        with op_tab2:
            ic1, ic2 = st.columns([1, 2])
            with ic1:
                st.markdown("#### Update Stock")
                with st.form("inv_form"):
                    inv_item = st.selectbox("Material", ["Cement", "Sand (Tons)", "Granite (Tons)", "Blocks (9 inch)", "Blocks (6 inch)", "Iron Rods (16mm)", "Iron Rods (12mm)"])
                    inv_qty = st.number_input("Quantity", min_value=0.1, step=1.0)
                    inv_unit = "Bags" if "Cement" in inv_item else "Pcs" if "Blocks" in inv_item else "Tons"
                    inv_action = st.radio("Action", ["📥 Stock IN (Delivery)", "📤 Stock OUT (Usage)"])
                    
                    if st.form_submit_button("Update Inventory"):
                        op = 'add' if "IN" in inv_action else 'remove'
                        success, msg = update_inventory(current_proj, inv_item, inv_qty, inv_unit, op)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            with ic2:
                st.markdown("#### 📋 Current Stock Level")
                if not inventory_df.empty:
                    inv_chart = alt.Chart(inventory_df).mark_bar().encode(
                        x='Quantity', y=alt.Y('Item', sort='-x'), color=alt.value("#27ae60"), tooltip=['Item', 'Quantity', 'Unit']
                    ).properties(height=300)
                    st.altair_chart(inv_chart, use_container_width=True)
                    
                    with st.expander("📜 Transaction History"):
                        st.dataframe(history_df, use_container_width=True)
                    
                    inv_pdf = generate_inventory_pdf(current_proj, inventory_df, history_df)
                    st.download_button("📥 Download Inventory Report", inv_pdf, "inventory.pdf", "application/pdf")
                else:
                    st.info("Inventory is empty. Add stock to see charts.")

        with op_tab3:
            dc1, dc2 = st.columns([1, 2])
            with dc1:
                st.markdown("#### New Daily Entry")
                with st.form("diary_form"):
                    w_cond = st.selectbox("Weather", ["☀️ Sunny", "🌥️ Cloudy", "🌧️ Rainy (Work Stopped)", "⛈️ Stormy"])
                    
                    st.markdown("**Labor Force**")
                    c_mas = st.number_input("Masons", 0, 20, 0)
                    c_lab = st.number_input("Laborers", 0, 50, 0)
                    c_iro = st.number_input("Iron Benders", 0, 20, 0)
                    
                    st.markdown("**Progress**")
                    work_done = st.text_area("Work Accomplished")
                    issues = st.text_area("Issues / Delays")
                    
                    if st.form_submit_button("💾 Submit Report"):
                        workers = {"Mason": c_mas, "Laborer": c_lab, "Iron Bender": c_iro}
                        log_site_diary(current_proj, w_cond, workers, work_done, issues)
                        st.success("Diary Saved")
                        st.rerun()

            with dc2:
                st.markdown("#### 📜 Site Diary History")
                if not diary_df.empty:
                    st.dataframe(
                        diary_df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                            "Weather": "Condition",
                            "Labor": "Workers",
                            "Work Done": "Progress",
                            "Issues": "Blockers"
                        }
                    )
                    pdf = generate_diary_pdf(current_proj, diary_df)
                    st.download_button("📥 Download DSR Report (PDF)", pdf, "site_report.pdf", "application/pdf")
                else:
                    st.info("No daily reports submitted yet.")