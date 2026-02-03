import streamlit as st
import sys
import os

# Add parent directory to path so we can import 'logic'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.db_manager import register_supplier, init_db

# Ensure DB exists
init_db()

st.set_page_config(page_title="Supplier Portal", page_icon="👷", layout="centered")

st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=50)
st.title("👷 Supplier Registration")
st.markdown("""
**Join the SiteMate Network.** Register your business to receive direct orders from engineers and project managers in your area.
""")

st.divider()

with st.form("supplier_signup_form"):
    st.subheader("🏢 Business Details")
    
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name", placeholder="e.g. Dangote Depo Lekki")
        location = st.selectbox("Operating Base", ["Lekki, Lagos", "Ibadan, Oyo", "Abuja, FCT"])
    
    with col2:
        phone = st.text_input("WhatsApp Number", placeholder="234...")
        email = st.text_input("Email Address", placeholder="sales@company.com")
    
    st.subheader("📦 Inventory")
    st.caption("Select the materials you can supply immediately:")
    
    materials = st.multiselect(
        "Materials Offered",
        ["Cement", "Sharp Sand", "Granite", "Iron Rods", "Blocks", "Roofing Sheets", "Paint"],
        default=["Cement", "Sharp Sand"]
    )
    
    agree = st.checkbox("I agree to the SiteMate Vendor Terms & Conditions")
    
    submitted = st.form_submit_button("🚀 Register Business", type="primary")

    if submitted:
        if not company_name or not phone or not agree:
            st.error("Please fill in all required fields and accept terms.")
        else:
            success = register_supplier(company_name, location, phone, email, materials)
            if success:
                st.balloons()
                st.success(f"✅ **Success!** {company_name} has been registered in {location}.")
                st.info("You will now appear in the Marketplace tab when engineers search in your area.")
            else:
                st.error("Database Error. Please try again.")