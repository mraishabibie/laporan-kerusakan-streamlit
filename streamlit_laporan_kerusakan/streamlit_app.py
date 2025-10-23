import streamlit as st
from database import db

# --- Konfigurasi ---
USERNAME = "staffdpagls" 
PASSWORD = "gls@123" 

st.set_page_config(
    page_title="Sistem Laporan Kerusakan Kapal",
    layout="wide"
)

# --- Inisialisasi Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_ship_code' not in st.session_state:
    st.session_state.selected_ship_code = None
if 'username' not in st.session_state:
    st.session_state.username = ""

# --- MAIN LOGIC ---
if not st.session_state.logged_in:
    st.title("🚢 Login Sistem Laporan Kerusakan")
    
    # --- CSS Kustom untuk Tampilan Login ---
    st.markdown("""
        <style>
            .stApp {
                background-color: #F0F2F6;
            }
            .stForm {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 30px;
                margin: 50px auto;
                width: 400px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); 
            }
            .stForm .stButton>button {
                background-color: #005691;
                color: white;
                border-radius: 8px;
                height: 40px;
                margin-top: 15px;
            }
            .stForm .stButton>button:hover {
                background-color: #004070;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.form("login_form"): 
        st.subheader("Masukkan ID dan Password Anda")
        username_input = st.text_input("ID Pengguna", key="user_input")
        password_input = st.text_input("Password", type="password", key="pass_input")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username_input == USERNAME and password_input == PASSWORD:
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success("Login Berhasil! Mengalihkan ke Homepage...")
                st.rerun()
            else:
                st.error("ID atau Password salah.")
else:
    # Main app navigation setelah login
    st.sidebar.title(f"⚓ Selamat datang, {st.session_state.username}!")
    
    # Navigation menu
    st.sidebar.markdown("### Navigasi")
    page = st.sidebar.radio(
        "Pilih Halaman:",
        ["Homepage", "Laporan Aktif & Input", "Analisis Dashboard", "Migrasi Data"]
    )
    
    # Migration option hanya untuk admin
    if st.session_state.username == USERNAME:
        if page == "Migrasi Data":
            # Import and run migration app
            from migrate_csv_to_sqlite import migrate_csv_to_sqlite_app
            migrate_csv_to_sqlite_app()
        elif page == "Homepage":
            st.switch_page("pages/1_Homepage.py")
        elif page == "Laporan Aktif & Input":
            st.switch_page("pages/2_Laporan_Aktif_&_Input.py")
        elif page == "Analisis Dashboard":
            st.switch_page("pages/3_Analisis_Dashboard.py")
    else:
        # Untuk user biasa, hide migration option
        if page == "Homepage":
            st.switch_page("pages/1_Homepage.py")
        elif page == "Laporan Aktif & Input":
            st.switch_page("pages/2_Laporan_Aktif_&_Input.py")
        elif page == "Analisis Dashboard":
            st.switch_page("pages/3_Analisis_Dashboard.py")