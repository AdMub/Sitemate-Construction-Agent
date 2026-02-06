import streamlit as st
import time

def require_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        # --- LOGIN SCREEN CSS ---
        st.markdown("""
        <style>
        .stApp { background-color: #0e1117; }
        .login-box { 
            border: 1px solid #333; padding: 40px; border-radius: 10px; 
            background-color: #161b22; text-align: center; max-width: 400px; margin: 0 auto;
        }
        </style>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.image("https://cdn-icons-png.flaticon.com/512/2666/2666505.png", width=80)
            st.title("SiteMate Pro")
            st.caption("Enterprise Construction OS")
            
            with st.form("login"):
                user = st.text_input("Username", placeholder="admin")
                pw = st.text_input("Password", type="password", placeholder="admin123")
                if st.form_submit_button("🚀 Enter Command Center", use_container_width=True):
                    # SUPER ADMIN (SEES EVERYTHING)
                    if user == "admin" and pw == "admin123":
                        st.session_state.authenticated = True
                        st.session_state.role = "Chief Engineer"
                        st.session_state.user_name = "Chief Engineer"
                        st.session_state.permissions = ["plan", "bid", "supply", "site"]
                        st.rerun()
                    
                    # SUPPLIER (RESTRICTED)
                    elif user == "vendor" and pw == "vendor123":
                        st.session_state.authenticated = True
                        st.session_state.role = "Supplier"
                        st.session_state.user_name = "AdMub Depot"
                        st.session_state.permissions = ["supply"]
                        st.rerun()

                    # SITE MANAGER (RESTRICTED)
                    elif user == "site" and pw == "site123":
                        st.session_state.authenticated = True
                        st.session_state.role = "Site Manager"
                        st.session_state.user_name = "Site Manager Tunde"
                        st.session_state.permissions = ["site"]
                        st.rerun()
                    else:
                        st.error("Invalid Access Credentials")
        st.stop()

def logout():
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.permissions = []
    st.rerun()