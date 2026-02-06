import streamlit as st
import pandas as pd
import altair as alt
import time

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="SiteMate Pro", page_icon="🏗️", layout="wide", initial_sidebar_state="expanded")

# --- 2. IMPORTS ---
from streamlit_mic_recorder import mic_recorder
from logic.transcriber import transcribe_audio
from logic.oyenuga_logic import get_agent_response
from logic.data_fetcher import get_live_price, get_suppliers_for_location
from logic.report_generator import generate_pdf_report, generate_diary_pdf
from logic.integrations import get_whatsapp_link, get_email_link
from logic.labor_engine import calculate_labor_cost
from logic.timeline_engine import calculate_project_timeline
from logic.db_manager import (
    init_db, save_project, get_all_projects, load_project_data, delete_project, 
    get_bids_for_project, register_supplier, get_open_tenders, submit_bid,
    log_expense, get_project_expenses, update_inventory, get_project_inventory, 
    get_inventory_logs, log_site_diary, get_site_diary, 
    get_all_supplier_names, update_bid_status, get_supplier_bids # Added new imports
)
from logic.weather_engine import get_site_weather
from logic.expert_verifier import verify_project_budget 
from logic.feasibility_engine import check_feasibility 
from logic.auth import require_auth, logout 

# --- 3. CUSTOM STYLING ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stSidebar"] { background-color: #1E1E1E; border-right: 1px solid #333; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; color: #888; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #FF8C00; border-bottom: 2px solid #FF8C00; }
</style>
""", unsafe_allow_html=True)

init_db()

# --- 4. AUTHENTICATION ---
require_auth()

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
    st.markdown("### **SiteMate Pro**")
    st.caption("Enterprise OS | v2.3 (Final)")
    
    st.markdown(f"""
    <div style='background-color: #2b313e; padding: 10px; border-radius: 5px; margin-bottom: 20px;'>
        <small>Logged in as:</small><br>
        <strong>{st.session_state['user_name']}</strong><br>
        <span style='color: #00FF00; font-size: 0.8em;'>● Online</span>
    </div>
    """, unsafe_allow_html=True)

    # --- GLOBAL CONTEXT ---
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
        <div style="background-color: #262730; color: #fff; padding: 10px; border-radius: 8px; border-left: 4px solid #FF8C00; margin-bottom: 15px;">
            <b>🌤️ Weather:</b> {weather_data['temp']}°C | {weather_data['condition']}
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

    # --- RESTORED: WHAT-IF & EXPERT VERIFICATION ---
    with p_tab2:
        st.subheader("⚡ Risk Analysis & Scenarios")
        
        if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
            
            # 1. WHAT-IF SCENARIOS
            c1, c2 = st.columns(2)
            with c1: steel_var = st.slider("📉 Steel Price Variance", -10, 20, 0, format="%d%%")
            with c2: concrete_grade = st.radio("🏗️ Concrete Grade", ["M20 (Standard)", "M25 (Heavy Duty)"])

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

            # 2. RESTORED: EXPERT VERIFICATION SERVICE
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
        
        # 1. PROJECT LOADER (LOAD / DELETE)
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
                # --- NEW DELETE BUTTON ---
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
                        
                        # AI JUDGMENT
                        if est_total > 0:
                            diff = ((bid['amount'] - est_total) / est_total) * 100
                            if abs(diff) <= 10: st.success(f"✅ Fair Price (Within {diff:.1f}% of AI Estimate)")
                            elif diff > 10: st.warning(f"⚠️ High Bid (+{diff:.1f}%)")
                            else: st.warning(f"📉 Suspiciously Low ({diff:.1f}%)")
                            
                    with c2:
                        st.metric("Bid Amount", f"₦{bid['amount']:,.0f}")
                        st.caption(f"Status: **{bid['status']}**")
                    
                    with c3:
                         # ACCEPT / REJECT LOGIC
                         if bid['status'] == 'Pending':
                             if st.button("✅ Accept", key=f"acc_{bid['id']}"):
                                 update_bid_status(bid['id'], "Accepted")
                                 st.rerun()
                             
                             if st.button("❌ Reject", key=f"rej_{bid['id']}"):
                                 update_bid_status(bid['id'], "Rejected")
                                 st.rerun()
                         
                         elif bid['status'] == 'Accepted':
                             st.success("Accepted!")
                             st.link_button("💳 Pay Now", "https://paystack.com/pay/sitemate-demo")
                         
                         elif bid['status'] == 'Rejected':
                             st.error("Rejected")

        st.divider()

        # --- SECTION 2: STANDARD SUPPLIERS (RESTORED) ---
        st.markdown("### 📚 Standard Suppliers Directory")
        st.caption("Contact registered suppliers directly if you don't want to wait for bids.")
        
        # Logic: If we have a BOQ, show estimated quotes from standard suppliers
        if 'boq_df' in st.session_state and not st.session_state['boq_df'].empty:
            base_total = st.session_state['boq_df']['Total Cost'].sum()
            suppliers = get_suppliers_for_location(selected_loc) # Fetches from DB
            
            if not suppliers:
                st.warning("No suppliers registered in this location yet.")
            else:
                for sup in suppliers:
                    # Simple logic: Supplier Quote = Base Cost * Markup (e.g. 1.1)
                    supplier_total = base_total * sup.get('markup', 1.05)
                    
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 2])
                        with c1:
                            st.markdown(f"**{sup['name']}**")
                            st.caption(f"⭐ {sup.get('rating', 'New')} | 📍 {selected_loc}")
                            st.write(f"**Est. Quote:** ₦{supplier_total:,.0f}")
                        with c2:
                            # WhatsApp Link
                            st.link_button("📲 Chat", get_whatsapp_link(sup.get('phone', '000'), "Hello, I have a project..."))
                        with c3:
                            # Email Link
                            email_link = get_email_link(sup.get('email', 'test@test.com'), selected_loc, "Order Inquiry")
                            if email_link: 
                                st.markdown(f'<a href="{email_link}" target="_blank" style="text-decoration:none;"><button style="width:100%; padding: 0.5rem; background-color: #f0f2f6; border: 1px solid #ccc; border-radius: 5px;">📧 Send Email</button></a>', unsafe_allow_html=True)
        else:
            st.info("Create a BOQ in the Planning tab to see supplier estimates.")

# ==========================================
# 🚚 TAB 3: SUPPLIER PORTAL (The "Vendor" View)
# ==========================================
elif selected_nav == "🚚 Supplier Portal":
    st.title("🚚 Supplier Portal")
    
    # --- 1. DEMO IMPERSONATION (DROPDOWN FIXED) ---
    active_user = st.session_state['user_name']
    
    if st.session_state.get('role') == "Chief Engineer":
        st.info("👮 **Admin Mode:** You are impersonating a supplier.")
        
        # FETCH REGISTERED SUPPLIERS FOR DROPDOWN
        registered_suppliers = get_all_supplier_names()
        active_user = st.selectbox("Simulate As:", registered_suppliers)
    # ---------------------------------------------
    
    s_tab1, s_tab2, s_tab3 = st.tabs(["💰 Job Board", "📂 My Bids (Status)", "📝 New Registration"])
    
    # --- JOB BOARD ---
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

    # --- NEW: MY BIDS (TRACKING) ---
    with s_tab2:
        st.markdown(f"### 📂 Bid History for {active_user}")
        my_bids = get_supplier_bids(active_user)
        
        if not my_bids:
            st.info("You haven't submitted any bids yet.")
        else:
            for bid in my_bids:
                status = bid['status'] # Pending, Accepted, Rejected
                color = "orange" if status == "Pending" else "green" if status == "Accepted" else "red"
                
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**Project:** {bid['project_name']}")
                        st.caption(f"Bid Amount: ₦{bid['amount']:,.0f} | Date: {bid['timestamp']}")
                    with c2:
                        st.markdown(f":{color}[**{status}**]")

    # --- REGISTRATION ---
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
                    st.rerun() # Refresh to update dropdown

# ==========================================
# 🚧 TAB 4: SITE OPERATIONS (The "Site Manager" View)
# ==========================================
elif selected_nav == "🚧 Site Operations":
    st.title("🚧 Site Execution Manager")
    
    # --- DEMO IMPERSONATION ---
    logger_name = "Site Manager"
    if st.session_state.get('role') == "Chief Engineer":
        st.info("👮 **Admin Mode:** Logging site data as 'Site Manager Tunde'.")
        logger_name = "Site Manager Tunde"
    # --------------------------

    current_proj = st.session_state.get('current_project_name')
    if not current_proj: st.error("Please load a project in the 'Planning' tab first.")
    else:
        st.success(f"Managing Site: **{current_proj}**")
        op_tab1, op_tab2, op_tab3 = st.tabs(["💸 Expense Log", "📦 Inventory", "📅 Daily Diary"])
        
        with op_tab1:
            with st.form("exp_form"):
                e_item = st.text_input("Item", placeholder="e.g. Diesel")
                e_amt = st.number_input("Amount", min_value=0)
                if st.form_submit_button("Log Expense"):
                    # Use 'logger_name' instead of Admin
                    log_expense(current_proj, e_item, e_amt, "Misc", f"Logged by {logger_name}")
                    st.success("Saved to Ledger")
            df_exp = get_project_expenses(current_proj)
            if not df_exp.empty: st.dataframe(df_exp, use_container_width=True)
            
        with op_tab3: 
            st.markdown("### 📝 Daily Site Report")
            w_cond = st.selectbox("Weather", ["Sunny", "Rainy", "Cloudy"])
            work_done = st.text_area("Work Done Today")
            if st.button("Submit Report"):
                log_site_diary(current_proj, w_cond, {}, work_done, "")
                st.success("Diary Saved")
            
            diary_df = get_site_diary(current_proj)
            if not diary_df.empty:
                pdf = generate_diary_pdf(current_proj, diary_df)
                st.download_button("📥 Download PDF Report", pdf, "site_report.pdf", "application/pdf")