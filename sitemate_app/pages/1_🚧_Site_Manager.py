import streamlit as st
import pandas as pd
import altair as alt
import sys
import os

# Path fix to ensure we can import from the 'logic' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.db_manager import get_all_projects, load_project_data, log_expense, get_project_expenses, update_inventory, get_project_inventory, get_inventory_logs
from logic.report_generator import generate_expense_pdf, generate_inventory_pdf 

st.set_page_config(page_title="Site Manager", page_icon="🚧", layout="wide")

st.title("🚧 Site Execution Manager")
st.caption("Track daily spending and material inventory.")

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
history_df = get_inventory_logs(selected_proj) # <--- This loads the missing history data

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
tab_finance, tab_inventory = st.tabs(["💵 Financial Ledger", "📦 Material Store"])

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
        
        # Export Button (Expenses)
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
            # Chart
            inv_chart = alt.Chart(inventory_df).mark_bar().encode(
                x='Quantity',
                y=alt.Y('Item', sort='-x'),
                color=alt.value("#27ae60"),
                tooltip=['Item', 'Quantity', 'Unit']
            ).properties(height=300)
            st.altair_chart(inv_chart, use_container_width=True)
            
            # History Table
            if not history_df.empty:
                with st.expander("📜 View Transaction History (Log)", expanded=False):
                    st.dataframe(history_df, hide_index=True, use_container_width=True)
            
            # Download Report (FIXED LINE BELOW)
            st.divider()
            inv_pdf_bytes = generate_inventory_pdf(selected_proj, inventory_df, history_df) # <--- Fixed: Added history_df
            st.download_button(
                label="📥 Download Inventory Audit Report (PDF)", 
                data=inv_pdf_bytes, 
                file_name=f"{selected_proj}_Inventory.pdf", 
                mime="application/pdf", 
                type="primary",
                use_container_width=True
            )
        else:
            st.info("Inventory is empty. Record a delivery (Stock IN) to start.")