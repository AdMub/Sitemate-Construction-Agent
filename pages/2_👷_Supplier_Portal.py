import streamlit as st
import sys
import os

# Path fix to find 'logic' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.db_manager import register_supplier, init_db, get_all_supplier_names, get_open_tenders, submit_bid
from logic.payment_gateway import initialize_payment # <--- Integrated Payment Logic

init_db()

st.set_page_config(page_title="Supplier Portal", page_icon="👷", layout="centered")

st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
st.title("👷 Supplier Portal")
st.caption("Register your business or bid on open construction projects.")

# TABS for separate functions
tab1, tab2 = st.tabs(["📝 New Registration", "💰 Job Board (Live Tenders)"])

# --- TAB 1: REGISTRATION ---
with tab1:
    st.subheader("Join the Network")
    st.markdown("Create a profile to be visible to engineers.")
    
    with st.form("reg_form"):
        col1, col2 = st.columns(2)
        with col1:
            c_name = st.text_input("Company Name", placeholder="e.g. Dangote Depot")
            c_loc = st.selectbox("Base Location", ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"])
        with col2:
            c_phone = st.text_input("WhatsApp", placeholder="234...")
            c_email = st.text_input("Email", placeholder="sales@...")
            
        c_mat = st.multiselect("Supply Items", ["Cement", "Sharp Sand", "Granite", "Iron Rods", "Blocks", "Paint"])
        
        if st.form_submit_button("Register Business"):
            if c_name and c_phone:
                if register_supplier(c_name, c_loc, c_phone, c_email, c_mat):
                    st.success(f"✅ {c_name} Registered Successfully!")
                    st.balloons()
                else:
                    st.error("Database Error. Try again.")
            else:
                st.warning("Please fill in Company Name and Phone.")

# --- TAB 2: BIDDING SYSTEM ---
with tab2:
    st.subheader("📋 Open Tenders")
    st.markdown("Find active projects in your area and submit your best price.")
    
    # 1. Select Identity (Login Simulation)
    suppliers = get_all_supplier_names()
    
    if not suppliers:
        st.warning("⚠️ No suppliers registered yet. Please go to Tab 1 to register.")
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            me = st.selectbox("Login as:", suppliers)
        with col_b:
            my_loc = st.selectbox("Filter Jobs by Location:", ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"])
        
        st.divider()
        
        # 2. Find Jobs
        jobs = get_open_tenders(my_loc)
        
        if jobs:
            st.success(f"Found {len(jobs)} active projects in {my_loc}")
            
            for job in jobs:
                with st.expander(f"🏗️ {job['name']} (Est. Value: ₦{job['est_value']:,.0f})"):
                    st.write(f"**Date Posted:** {job['date']}")
                    st.write(f"**Materials Needed:** {job['items']} unique items (Cement, Sand, etc.)")
                    
                    # 3. Submit Bid Form
                    st.markdown("#### Submit Your Quote")
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        bid_val = st.number_input(f"Total Bid Amount (₦)", min_value=0.0, step=1000.0, key=f"bid_{job['name']}")
                    with c2:
                        st.write("") # Spacer
                        st.write("") # Spacer
                        submit_btn = st.button(f"🚀 Submit Bid", key=f"btn_{job['name']}")
                    
                    if submit_btn:
                        if bid_val > 0:
                            if submit_bid(job['name'], me, bid_val, "234..."):
                                st.toast(f"✅ Bid sent for {job['name']}!")
                                st.success("Bid submitted! The engineer will contact you if accepted.")
                            else:
                                st.error("Failed to submit bid.")
                        else:
                            st.warning("Please enter a valid amount.")
        else:
            st.info("No open projects found in this location right now. Check back later.")