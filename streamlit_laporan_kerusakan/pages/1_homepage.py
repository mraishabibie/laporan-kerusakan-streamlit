import streamlit as st
import pandas as pd
from datetime import datetime
from database import db

# --- Logika Autentikasi Halaman ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Anda harus login untuk mengakses halaman ini. Silakan kembali ke halaman utama.")
    st.stop() 

DATE_FORMAT = '%d/%m/%Y'

def get_processed_data_for_display(selected_year=None):
    """Memuat, memproses, dan memfilter data dari SQLite - TANPA CACHE"""
    
    df = db.get_all_laporan()
    
    if df.empty:
        return pd.DataFrame(), 0, 0, []

    # Processing dates
    df['Date_Issued'] = pd.to_datetime(df['issued_date'], format='%d/%m/%Y', errors='coerce')
    
    # Filter by year if selected
    df_filtered = df.copy()
    if selected_year and selected_year != 'All':
        df_filtered = df_filtered[df_filtered['Date_Issued'].dt.year == int(selected_year)]

    total_open_global = (df_filtered['status'] == 'OPEN').sum()
    total_closed_global = (df_filtered['status'] == 'CLOSED').sum()

    # Group by vessel untuk stats
    stats = df_filtered.groupby('vessel')['status'].value_counts().unstack(fill_value=0)
    stats['OPEN'] = stats.get('OPEN', 0)
    stats['CLOSED'] = stats.get('CLOSED', 0)
    
    last_inspection = df.groupby('vessel')['Date_Issued'].max().dt.strftime(DATE_FORMAT)

    result = stats[['OPEN', 'CLOSED']].reset_index()
    result['last_inspection'] = result['vessel'].map(last_inspection)
    
    valid_years = df['Date_Issued'].dt.year.dropna().astype(int).unique().tolist()
    
    return result, total_open_global, total_closed_global, valid_years

# --- FUNGSI UTAMA UNTUK DATA CARD ---
def get_ship_list(df_stats):
    """Mengambil data status Open/Closed NC secara dinamis dari DataFrame statistik."""
    ship_list = []
    if not df_stats.empty:
        for _, row in df_stats.iterrows():
            ship_list.append({
                "code": row['vessel'],
                "open_nc": int(row['OPEN']),
                "closed_nc": int(row['CLOSED']),
                "last_inspection": row['last_inspection'] if pd.notna(row['last_inspection']) else 'N/A'
            })
    return ship_list

def filter_ship_list(ship_list, search_query, status_filter):
    """Filter daftar kapal berdasarkan search query dan status filter"""
    filtered_ships = ship_list
    
    # Filter berdasarkan search query
    if search_query:
        search_query = search_query.upper().strip()
        filtered_ships = [ship for ship in filtered_ships if search_query in ship['code'].upper()]
    
    # Filter berdasarkan status
    if status_filter != 'Semua Status':
        if status_filter == 'Ada Laporan OPEN':
            filtered_ships = [ship for ship in filtered_ships if ship['open_nc'] > 0]
        elif status_filter == 'Semua CLOSED':
            filtered_ships = [ship for ship in filtered_ships if ship['open_nc'] == 0 and ship['closed_nc'] > 0]
        elif status_filter == 'Belum Ada Laporan':
            filtered_ships = [ship for ship in filtered_ships if ship['open_nc'] == 0 and ship['closed_nc'] == 0]
    
    return filtered_ships

# --- FUNGSI DISPLAY CARD DENGAN HTML/CSS KUSTOM ---
def display_ship_cards(ship_list):
    """Menampilkan daftar kapal dalam format card kustom."""
    st.markdown("""
        <style>
            .ship-card-content {
                background-color: #FFFFFF; 
                border-radius: 12px 12px 0 0;
                padding: 20px;
                width: 100% !important; 
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15); 
                border-top: 5px solid #005691;
                transition: transform 0.2s ease-in-out;
            }
            .ship-card-content:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
            }
            .stButton>button {
                margin-top: 0px; 
                height: 40px;
                background-color: #005691;
                color: white;
                border: none;
                border-radius: 0 0 12px 12px;
                transition: background-color 0.2s;
            }
            .stButton>button:hover {
                background-color: #004070;
            }
            .ship-code-display {
                font-size: 1.5em;
                font-weight: bold;
                color: #111111;
                margin-bottom: 5px;
            }
            .nc-grid {
                display: flex;
                justify-content: space-between;
                margin-top: 15px;
            }
            .nc-item {
                text-align: center;
            }
            .nc-value-open {
                font-size: 1.8em;
                font-weight: bold;
                color: #FF4B4B;
            }
            .nc-value-closed {
                font-size: 1.8em;
                font-weight: bold;
                color: #00BA38;
            }
            .nc-label {
                font-size: 0.8em;
                color: #666666;
                margin-top: 5px;
            }
            .last-inspection {
                font-size: 0.8em;
                color: #777777;
                margin-top: 15px;
                border-top: 1px solid #DDDDDD; 
                padding-top: 8px;
            }
            .global-metric-box {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 15px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
                transition: transform 0.2s;
            }
            .global-metric-box:hover {
                transform: translateY(-1px);
            }
            .global-value-open {
                font-size: 2em;
                font-weight: bold;
                color: #FF4B4B;
            }
            .global-value-closed {
                font-size: 2em;
                font-weight: bold;
                color: #00BA38;
            }
            .global-value-total {
                font-size: 2em;
                font-weight: bold;
                color: #005691; 
            }
            .global-label {
                font-size: 0.9em;
                color: #555555;
            }
            .search-container {
                background-color: #FFFFFF;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .filter-badge {
                display: inline-block;
                background-color: #005691;
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                margin: 2px;
            }
        </style>
    """, unsafe_allow_html=True)

    if not ship_list:
        st.warning("🚫 Tidak ada kapal yang sesuai dengan filter pencarian.")
        return

    ship_list.sort(key=lambda x: x['code']) 
    num_cols = 3 
    cols = st.columns(num_cols)
    
    for i, ship in enumerate(ship_list):
        col = cols[i % num_cols]
        
        ship_name = ship['code']

        with col:
            # Tentukan warna border berdasarkan status
            border_color = "#005691"  # Default blue
            if ship['open_nc'] > 0 and ship['closed_nc'] > 0:
                border_color = "#FFA500"  # Orange for mixed status
            elif ship['open_nc'] > 0:
                border_color = "#FF4B4B"  # Red for has OPEN reports
            elif ship['closed_nc'] > 0:
                border_color = "#00BA38"  # Green for all CLOSED
            
            card_html = f"""
                <div class="ship-card-content" style="border-top: 5px solid {border_color};">
                    <div class="ship-code-display">{ship_name}</div>
                    <div style="font-size: 0.9em; color: #777;">Kode Kapal: {ship['code']}</div>
                    <div class="nc-grid">
                        <div class="nc-item">
                            <div class="nc-value-open">{ship['open_nc']}</div>
                            <div class="nc-label">Laporan Open</div>
                        </div>
                        <div class="nc-item">
                            <div class="nc-value-closed">{ship['closed_nc']}</div>
                            <div class="nc-label">Laporan Closed</div>
                        </div>
                    </div>
                    <div class="last-inspection">
                        Terakhir Update: {ship['last_inspection']}
                    </div>
                </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            if st.button(f"Lihat Detail {ship['code']}", key=f"btn_{ship['code']}_{i}", use_container_width=True):
                st.session_state.selected_ship_code = ship['code']
                st.session_state.selected_ship_name = ship_name 
                st.switch_page("pages/2_Laporan_Aktif_&_Input.py")
                
            st.markdown(f'<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)

# --- MAIN LOGIC ---
st.set_page_config(page_title="Homepage", layout="wide")

st.sidebar.success(f"Selamat Datang, {st.session_state.username}!")

# --- HEADER DENGAN REFRESH ---
col_title, col_refresh = st.columns([4, 1])
with col_title:
    st.markdown("# Homepage")
    st.markdown("## Laporan Kerusakan Kapal")
with col_refresh:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

st.write("---")

# --- FILTER UTAMA ---
df_stats_temp, _, _, valid_years_list_temp = get_processed_data_for_display()
year_options = ['All'] + sorted(valid_years_list_temp, reverse=True)

# --- SEARCH AND FILTER SECTION ---
st.markdown("### 🔍 Cari & Filter Kapal")

with st.container():
    col_search, col_status, col_year = st.columns([2, 1.5, 1])
    
    with col_search:
        search_query = st.text_input(
            "Cari nama kapal...",
            placeholder="Masukkan nama kapal...",
            key="search_ship"
        )
    
    with col_status:
        status_options = ['Semua Status', 'Ada Laporan OPEN', 'Semua CLOSED', 'Belum Ada Laporan']
        status_filter = st.selectbox(
            "Filter Status",
            options=status_options,
            key="status_filter"
        )
    
    with col_year:
        selected_year = st.selectbox("Filter Tahun", year_options, key="filter_tahun_homepage")

# --- LOAD DATA (SETELAH FILTER DITERAPKAN) ---
df_stats, total_open, total_closed, _ = get_processed_data_for_display(selected_year)

# --- MENAMPILKAN METRIK GLOBAL ---
st.markdown("### 📊 Ringkasan Status Global")

col_open, col_closed, col_total, col_filtered = st.columns(4)

with col_open:
    st.markdown(f"""
        <div class="global-metric-box" style="border-top: 5px solid #FF4B4B;">
            <div class="global-label">TOTAL LAPORAN OPEN</div>
            <div class="global-value-open">{total_open}</div>
        </div>
    """, unsafe_allow_html=True)

with col_closed:
    st.markdown(f"""
        <div class="global-metric-box" style="border-top: 5px solid #00BA38;">
            <div class="global-label">TOTAL LAPORAN CLOSED</div>
            <div class="global-value-closed">{total_closed}</div>
        </div>
    """, unsafe_allow_html=True)

with col_total:
    st.markdown(f"""
        <div class="global-metric-box" style="border-top: 5px solid #005691;">
            <div class="global-label">TOTAL SELURUH LAPORAN</div>
            <div class="global-value-total">{total_open + total_closed}</div>
        </div>
    """, unsafe_allow_html=True)

with col_filtered:
    # Hitung jumlah kapal setelah filter
    if df_stats.empty:
        filtered_ship_count = 0
    else:
        final_ship_list = get_ship_list(df_stats)
        filtered_ships = filter_ship_list(final_ship_list, search_query, status_filter)
        filtered_ship_count = len(filtered_ships)
    
    st.markdown(f"""
        <div class="global-metric-box" style="border-top: 5px solid #8B5CF6;">
            <div class="global-label">KAPAL DITEMUKAN</div>
            <div class="global-value-total">{filtered_ship_count}</div>
        </div>
    """, unsafe_allow_html=True)

# --- TAMPILAN FILTER AKTIF ---
if search_query or status_filter != 'Semua Status':
    st.markdown("#### 🎯 Filter Aktif:")
    filter_info = ""
    if search_query:
        filter_info += f"<span class='filter-badge'>Pencarian: '{search_query}'</span> "
    if status_filter != 'Semua Status':
        filter_info += f"<span class='filter-badge'>Status: {status_filter}</span> "
    if selected_year != 'All':
        filter_info += f"<span class='filter-badge'>Tahun: {selected_year}</span>"
    
    st.markdown(filter_info, unsafe_allow_html=True)

st.markdown("---")

# --- TAMPILAN CARD KAPAL DENGAN FILTER ---
st.markdown(f"### 🚢 Daftar Kapal ({filtered_ship_count} kapal ditemukan)")

if df_stats.empty:
    st.warning("Tidak ada data kapal yang valid ditemukan untuk filter ini.")
else:
    final_ship_list = get_ship_list(df_stats)
    filtered_ships = filter_ship_list(final_ship_list, search_query, status_filter)
    display_ship_cards(filtered_ships)

# --- FOOTER INFO ---
st.markdown("---")
col_info, col_actions = st.columns([3, 1])

with col_info:
    st.info("""
    **ℹ️ Legend Warna Border Kartu:**
    - 🔵 **Biru**: Default / belum ada laporan
    - 🔴 **Merah**: Memiliki laporan OPEN
    - 🟢 **Hijau**: Semua laporan CLOSED  
    - 🟠 **Oranye**: Campuran OPEN & CLOSED
    """)

with col_actions:
    if st.button("🧹 Reset Filter", use_container_width=True):
        st.session_state.search_ship = ""
        st.session_state.status_filter = "Semua Status"
        st.session_state.filter_tahun_homepage = "All"
        st.rerun()