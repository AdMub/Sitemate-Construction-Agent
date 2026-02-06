import streamlit as st
import pandas as pd
import altair as alt
import sys
import os

# Path fix
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.db_manager import (
    get_all_projects, load_project_data, log_expense, get_project_expenses, 
    update_inventory, get_project_inventory, get_inventory_logs, 
    log_site_photo, get_site_photos,
    log_site_diary, get_site_diary
)
# IMPORT THE NEW FUNCTION HERE
from logic.report_generator import generate_expense_pdf, generate_inventory_pdf, generate_diary_pdf 

st.set_page_config(page_title="Site Manager", page_icon="🚧", layout="wide")

st.title("🚧 Site Execution Manager")
st.caption("Track daily spending, inventory, logs, and site progress.")

# 1. SELECT PROJECT
projects = get_all_projects()
if not projects:
    st.warning("No projects found. Create one in the Main App first.")
    st.stop()

project_names = [p[0] for p in projects]
selected_proj = st.selectbox("Select Active Site:", project_names)

# Load Data
loc, soil, plan_df = load_project_data(selected_proj)
actual_df = get_project_expenses(selected_proj)
inventory_df = get_project_inventory(selected_proj)
history_df = get_inventory_logs(selected_proj)
diary_df = get_site_diary(selected_proj) # Load Diary

# 2. TOP METRICS
planned_total = plan_df['Total Cost'].sum() if plan_df is not None else 0
spent_total = actual_df['amount'].sum() if not actual_df.empty else 0
remaining = planned_total - spent_total

col1, col2, col3 = st.columns(3)
col1.metric("💰 Planned Budget", f"₦{planned_total:,.0f}")
col2.metric("💸 Actual Spent", f"₦{spent_total:,.0f}", delta=f"-{(spent_total/planned_total)*100:.1f}% used" if planned_total else "0%")
col3.metric("📉 Remaining", f"₦{remaining:,.0f}", delta_color="normal" if remaining > 0 else "inverse")

st.divider()

# TABS FOR MANAGEMENT
tab_finance, tab_inventory, tab_gallery, tab_diary = st.tabs(["💵 Ledger", "📦 Material Store", "📸 Gallery", "📅 Daily Diary"])

# --- TAB 1: FINANCIAL LEDGER ---
with tab_finance:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("📝 Log Expense")
        with st.form("expense_form"):
            item = st.text_input("Item / Service", placeholder="e.g. Labor Payment")
            amt = st.number_input("Amount (₦)", min_value=0.0, step=1000.0)
            cat = st.selectbox("Category", ["Materials", "Labor", "Logistics", "Permits", "Misc"])
            note = st.text_area("Note", placeholder="Receipt #...")
            
            if st.form_submit_button("💾 Save Expense"):
                if log_expense(selected_proj, item, amt, cat, note):
                    st.success("Saved!")
                    st.rerun()
                else:
                    st.error("Error.")
        
        if not actual_df.empty:
            st.divider()
            st.subheader("📄 Export Ledger")
            pdf_bytes = generate_expense_pdf(selected_proj, planned_total, actual_df)
            st.download_button("📥 Download Logbook (PDF)", pdf_bytes, f"{selected_proj}_Log.pdf", "application/pdf", type="primary", use_container_width=True)

    with c2:
        st.subheader("📊 Financial Health")
        if not actual_df.empty:
            chart = alt.Chart(actual_df).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("amount", stack=True), color=alt.Color("category"), tooltip=["category", "amount"]
            ).properties(title="Spending Breakdown")
            st.altair_chart(chart, use_container_width=True)
            st.caption("Recent Transactions")
            st.dataframe(actual_df[['date', 'item', 'category', 'amount']].sort_values('date', ascending=False), hide_index=True, use_container_width=True)
        else:
            st.info("No expenses logged yet.")

# --- TAB 2: INVENTORY STORE ---
with tab_inventory:
    st.subheader("🏗️ Site Inventory Control")
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
                success, msg = update_inventory(selected_proj, inv_item, inv_qty, inv_unit, op)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with ic2:
        st.markdown("#### 📋 Current Stock & History")
        if not inventory_df.empty:
            inv_chart = alt.Chart(inventory_df).mark_bar().encode(
                x='Quantity', y=alt.Y('Item', sort='-x'), color=alt.value("#27ae60"), tooltip=['Item', 'Quantity', 'Unit']
            ).properties(height=300)
            st.altair_chart(inv_chart, use_container_width=True)
            
            if not history_df.empty:
                with st.expander("📜 View Transaction History (Log)", expanded=False):
                    st.dataframe(history_df, hide_index=True, use_container_width=True)
            
            st.divider()
            inv_pdf_bytes = generate_inventory_pdf(selected_proj, inventory_df, history_df)
            st.download_button("📥 Download Inventory Report (PDF)", inv_pdf_bytes, f"{selected_proj}_Inventory.pdf", "application/pdf", type="primary", use_container_width=True)
        else:
            st.info("Inventory is empty.")

# --- TAB 3: SITE GALLERY ---
with tab_gallery:
    st.subheader("📸 Site Progress Evidence")
    with st.expander("Upload New Photo", expanded=False):
        uploaded_file = st.file_uploader("Capture/Upload Image", type=['jpg', 'png'])
        photo_caption = st.text_input("Caption", placeholder="e.g. Foundation Casting complete")
        if uploaded_file and st.button("Save Photo"):
            if log_site_photo(selected_proj, uploaded_file.getvalue(), photo_caption):
                st.success("Photo Uploaded!")
                st.rerun()

    photos = get_site_photos(selected_proj)
    if photos:
        cols = st.columns(3)
        for i, (path, cap, time) in enumerate(photos):
            with cols[i % 3]:
                if os.path.exists(path):
                    st.image(path, use_column_width=True) 
                    st.caption(f"**{time}**: {cap}")
    else:
        st.info("No site photos yet.")

# --- TAB 4: DAILY DIARY (UPDATED) ---
with tab_diary:
    st.subheader("📅 Daily Site Report (DSR)")
    
    dc1, dc2 = st.columns([1, 2])
    with dc1:
        with st.form("diary_form"):
            st.markdown("**Today's Conditions**")
            weather = st.selectbox("Weather", ["☀️ Sunny", "🌥️ Cloudy", "🌧️ Rainy (Work Stopped)", "⛈️ Stormy"])
            
            st.markdown("**Labor Force (Headcount)**")
            mason = st.number_input("Masons", 0, 50, 0)
            laborer = st.number_input("Laborers", 0, 50, 0)
            iron_bender = st.number_input("Iron Benders", 0, 50, 0)
            carpenter = st.number_input("Carpenters", 0, 50, 0)
            
            st.markdown("**Progress & Issues**")
            work_done = st.text_area("Work Accomplished", placeholder="e.g. Cast 5 columns...")
            issues = st.text_area("Issues / Delays", placeholder="e.g. Rain delay, Generator fault...")
            
            if st.form_submit_button("💾 Submit Daily Report"):
                workers = {"Mason": mason, "Laborer": laborer, "Iron Bender": iron_bender, "Carpenter": carpenter}
                success, msg = log_site_diary(selected_proj, weather, workers, work_done, issues)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with dc2:
        # --- NEW: CLEAN TABLE VIEW ---
        st.markdown("#### 📜 Site Diary History")
        
        if not diary_df.empty:
            # Display as a clean, interactive table
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
            
            # --- NEW: PDF DOWNLOAD BUTTON ---
            st.divider()
            diary_pdf_bytes = generate_diary_pdf(selected_proj, diary_df)
            st.download_button(
                label="📥 Download Site Diary Log (PDF)", 
                data=diary_pdf_bytes, 
                file_name=f"{selected_proj}_Site_Diary.pdf", 
                mime="application/pdf", 
                type="primary",
                use_container_width=True
            )
        else:
            st.info("No daily reports submitted yet. Use the form to submit today's log.")