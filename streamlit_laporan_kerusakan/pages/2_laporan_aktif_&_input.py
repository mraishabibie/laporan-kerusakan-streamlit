import streamlit as st
import pandas as pd
from datetime import datetime
import time 
import numpy as np 
from database import db

# --- Logika Autentikasi Halaman ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.error("Anda harus login untuk mengakses halaman ini. Silakan kembali ke halaman utama.")
    st.stop() 

# --- Cek Kapal Terpilih & Inisialisasi Variabel Kapal ---
if 'selected_ship_code' not in st.session_state or st.session_state.selected_ship_code is None:
    st.error("Anda harus memilih kapal dari halaman utama terlebih dahulu.")
    st.stop() 

SELECTED_SHIP_CODE = st.session_state.selected_ship_code
SELECTED_SHIP_NAME = st.session_state.get('selected_ship_name', SELECTED_SHIP_CODE)

# --- INISIALISASI SESSION STATE UNTUK INPUT DAN EDIT ---
if 'show_new_report_form_v2' not in st.session_state:
    st.session_state.show_new_report_form_v2 = False
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None 
if 'confirm_delete_id' not in st.session_state:
    st.session_state.confirm_delete_id = None 

# --- Konfigurasi Format ---
DATE_FORMAT = '%d/%m/%Y'

# -------------------------------------------------------------------------------------
# --- FUNGSI LOAD DATA (MEMBACA DARI SQLITE) ---
# -------------------------------------------------------------------------------------
def load_data():
    """Memuat data untuk kapal terpilih dari SQLite."""
    return db.get_laporan_by_vessel(SELECTED_SHIP_CODE)

def get_report_stats(df, year=None):
    """Menghitung total, open, dan closed report, difilter berdasarkan tahun."""
    df_filtered = df.copy()
    
    if year and year != 'All':
        df_filtered = df_filtered[df_filtered['Date_Day'].dropna().dt.year == int(year)]
        
    total = len(df_filtered)
    open_count = len(df_filtered[df_filtered['status'].str.upper() == 'OPEN'])
    closed_count = len(df_filtered[df_filtered['status'].str.upper() == 'CLOSED'])
    return total, open_count, closed_count, df_filtered

def add_new_data(new_entry):
    """Menambahkan baris data baru ke SQLite."""
    try:
        laporan_id = db.add_laporan(new_entry)
        st.success(f"✅ Laporan baru berhasil ditambahkan (ID: {laporan_id})")
        return True
    except Exception as e:
        st.error(f"❌ Gagal menambah laporan: {e}")
        return False

def delete_data(laporan_id):
    """Menghapus baris berdasarkan ID."""
    try:
        success = db.delete_laporan(laporan_id)
        if success:
            st.success(f"✅ Laporan dengan ID {laporan_id} berhasil dihapus.")
            st.session_state.confirm_delete_id = None
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Gagal menghapus laporan.")
    except Exception as e:
        st.error(f"❌ Error saat menghapus: {e}")

def start_delete_confirmation(unique_id):
    """Setel state untuk menampilkan modal konfirmasi."""
    st.session_state.confirm_delete_id = unique_id
    st.rerun()

# --- Fungsi Pembantu: Parsing Tanggal ---
def parse_date(date_str):
    if pd.isna(date_str) or str(date_str).strip() == '':
        return pd.NaT
    for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%y-%m-%d', '%Y/%m/%d', DATE_FORMAT]:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except (ValueError, TypeError):
            continue
    return pd.NaT

# --- Tampilan Utama ---
st.title(f'📝 Laporan Kerusakan Aktif & Input Data: {SELECTED_SHIP_NAME} ({SELECTED_SHIP_CODE})')

df_filtered_ship = load_data() 

# Processing dates untuk filtering
df_filtered_ship['Date_Day'] = df_filtered_ship['day'].apply(parse_date)
df_filtered_ship['Date_Issued'] = df_filtered_ship['issued_date'].apply(parse_date)

# Pastikan unit_options dibuat dari data yang sudah dimuat
unit_options = sorted(df_filtered_ship['unit'].dropna().unique().tolist())

# =========================================================
# === DASHBOARD STATISTIK DENGAN FILTER TAHUN ===
# =========================================================
valid_years = df_filtered_ship['Date_Day'].dropna().dt.year.astype(int).unique()
year_options = ['All'] + sorted(valid_years.tolist(), reverse=True)

with st.container(border=True): 
    col_filter, col_spacer_top = st.columns([1, 4])
    
    with col_filter:
        selected_year = st.selectbox("Filter Tahun Kejadian", year_options, key="filter_tahun_aktif")
        
    total_reports, open_reports, closed_reports, _ = get_report_stats(df_filtered_ship, selected_year)

    st.markdown("##### Ringkasan Status Laporan")
    
    col_total, col_open, col_closed, col_spacer = st.columns([1, 1, 1, 3]) 
    
    # --- CSS KUSTOM UNTUK METRIK ---
    st.markdown("""
        <style>
            .metric-box-custom {
                background-color: #F0F2F6;
                border-radius: 8px;
                padding: 10px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                min-height: 80px;
            }
            .metric-value-total {
                font-size: 2em;
                font-weight: bold;
                color: #005691;
            }
            .metric-value-open {
                font-size: 2em;
                font-weight: bold;
                color: #FF4B4B;
            }
            .metric-value-closed {
                font-size: 2em;
                font-weight: bold;
                color: #00BA38;
            }
            .metric-label-custom {
                font-size: 0.9em;
                color: #555555;
            }
        </style>
    """, unsafe_allow_html=True)

    with col_total:
        st.markdown(f"""
            <div class="metric-box-custom" style="border-left: 5px solid #005691;">
                <div class="metric-label-custom">Total Seluruh Laporan</div>
                <div class="metric-value-total">{total_reports}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_open:
        st.markdown(f"""
            <div class="metric-box-custom" style="border-left: 5px solid #FF4B4B;">
                <div class="metric-label-custom">Laporan Masih OPEN</div>
                <div class="metric-value-open">{open_reports}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col_closed:
        st.markdown(f"""
            <div class="metric-box-custom" style="border-left: 5px solid #00BA38;">
                <div class="metric-label-custom">Laporan Sudah CLOSED</div>
                <div class="metric-value-closed">{closed_reports}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---") 

# =========================================================
# === DATA AKTIF (CUSTOM DISPLAY, INLINE EDIT, & HAPUS) ===
# =========================================================

st.subheader("📋 Laporan Kerusakan Aktif (OPEN)")

confirmation_placeholder = st.empty()

if df_filtered_ship.empty:
    st.info("Belum ada data notulensi kerusakan tersimpan untuk kapal ini.")
else:
    df_active = df_filtered_ship[df_filtered_ship['status'].str.upper() == 'OPEN'].copy()

    if selected_year and selected_year != 'All':
          df_active = df_active[df_active['Date_Day'].dt.year == int(selected_year)]
          
    df_active = df_active.sort_values(by='Date_Day', ascending=False)
    
    # ------------------- HEADER CUSTOM TABLE ----------------------
    col_id, col_masalah, col_unit, col_status_date, col_action = st.columns([0.5, 3, 1, 1.5, 1.5])
    col_id.markdown('**ID**', unsafe_allow_html=True)
    col_masalah.markdown('**PERMASALAHAN / PENYELESAIAN**', unsafe_allow_html=True)
    col_unit.markdown('**UNIT**', unsafe_allow_html=True)
    col_status_date.markdown('**TGL KEJADIAN**', unsafe_allow_html=True)
    col_action.markdown('**AKSI**', unsafe_allow_html=True)
    st.markdown("---")

    for index, row in df_active.iterrows():
        laporan_id = row['id']
        is_editing = st.session_state.edit_id == laporan_id
        
        # --- DISPLAY MODE (READ-ONLY) ---
        if not is_editing:
            
            cols = st.columns([0.5, 3, 1, 1.5, 1.5])
            
            cols[0].write(f"**ID{int(laporan_id)}**")
            
            problem_text = f"**Masalah:** {str(row['permasalahan'])} | <small>Solusi: {str(row['penyelesaian'])}</small>"
            cols[1].markdown(problem_text, unsafe_allow_html=True)
            
            cols[2].write(row['unit'])
            
            date_text = f"**Tgl:** {row['day']}"
            cols[3].markdown(date_text, unsafe_allow_html=True)

            # --- ACTION BUTTONS (EDIT & HAPUS) ---
            action_col = cols[4]
            btn_edit, btn_delete = action_col.columns(2)
            
            if btn_edit.button("✏️ Edit", key=f"edit_{laporan_id}", use_container_width=True):
                st.session_state.edit_id = laporan_id
                st.rerun()
                
            if btn_delete.button("🗑️ Hapus", key=f"delete_{laporan_id}", use_container_width=True):
                start_delete_confirmation(laporan_id) 

        # --- EDIT MODE (INLINE FORM) ---
        else:
            with st.container(border=True):
                
                key_prefix = f"edit_form_{laporan_id}_"
                
                st.markdown(f"**Mengedit Laporan ID: ID{int(laporan_id)}**", unsafe_allow_html=True)
                
                col_id, col_masalah_solusi, col_unit, col_status_date, col_action = st.columns([0.5, 3, 1, 1.5, 1.5])
                
                col_id.write(f"**ID{int(laporan_id)}**") 
                
                new_permasalahan = col_masalah_solusi.text_area("Masalah", value=row['permasalahan'], height=50, key=key_prefix + 'permasalahan')
                new_penyelesaian = col_masalah_solusi.text_area("Solusi", value=row['penyelesaian'], height=50, key=key_prefix + 'penyelesaian')
                new_keterangan = col_masalah_solusi.text_input("Keterangan Tambahan", value=row['keterangan'], key=key_prefix + 'keterangan')
                
                default_unit_idx = unit_options.index(row['unit']) if row['unit'] in unit_options else 0
                new_unit = col_unit.selectbox("Unit", options=unit_options, index=default_unit_idx, key=key_prefix + 'unit')

                try:
                    default_day_dt = datetime.strptime(row['day'], DATE_FORMAT).date()
                except ValueError:
                    default_day_dt = datetime.now().date()
                    
                new_day = col_status_date.date_input("Tgl Kejadian (Day)", value=default_day_dt, key=key_prefix + 'day')
                
                default_status_idx = 1 if row['status'] == 'CLOSED' else 0
                new_status = col_status_date.selectbox("Status", options=['OPEN', 'CLOSED'], index=default_status_idx, key=key_prefix + 'status')
                
                new_closed_date = None
                if new_status == 'CLOSED':
                    current_closed_date_str = str(row['closed_date'])
                    current_closed_date_dt = None
                    if current_closed_date_str != 'nan' and current_closed_date_str != '':
                        try:
                            current_closed_date_dt = datetime.strptime(current_closed_date_str, DATE_FORMAT).date()
                        except ValueError:
                            current_closed_date_dt = None
                            
                    new_closed_date = col_status_date.date_input("Tgl Selesai (Jika Closed)", 
                                                                 value=current_closed_date_dt, 
                                                                 key=key_prefix + 'closed_date')
                
                action_col = col_action
                action_col.write("<br>", unsafe_allow_html=True) 
                btn_save, btn_cancel = action_col.columns(2)
                
                if btn_save.button("✅ Simpan", key=key_prefix + 'save', use_container_width=True):
                    
                    closed_date_val = ""
                    if new_status == 'CLOSED' and new_closed_date is not None:
                        closed_date_val = new_closed_date.strftime(DATE_FORMAT)
                    
                    updated_data = {
                        'Day': new_day.strftime(DATE_FORMAT),
                        'Vessel': SELECTED_SHIP_CODE,
                        'Permasalahan': new_permasalahan,
                        'Penyelesaian': new_penyelesaian,
                        'Keterangan': new_keterangan,
                        'Unit': new_unit,
                        'Status': new_status,
                        'Issued Date': new_day.strftime(DATE_FORMAT),
                        'Closed Date': closed_date_val
                    }
                    
                    try:
                        db.update_laporan(laporan_id, updated_data)
                        st.success("✅ Perubahan berhasil disimpan!")
                        st.session_state.edit_id = None
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Gagal menyimpan perubahan: {e}")

                if btn_cancel.button("❌ Batal", key=key_prefix + 'cancel', use_container_width=True):
                    st.session_state.edit_id = None
                    st.rerun()
        
            st.markdown("---") 

# =========================================================
# === LOGIKA MODAL KONFIRMASI HAPUS ===
# =========================================================

if st.session_state.confirm_delete_id is not None:
    delete_id = st.session_state.confirm_delete_id
    
    # Ambil detail laporan untuk ditampilkan di modal
    report_to_delete = df_filtered_ship[df_filtered_ship['id'] == delete_id]
    if not report_to_delete.empty:
        report_to_delete = report_to_delete.iloc[0]
        masalah = report_to_delete['permasalahan']
        unit = report_to_delete['unit']
    else:
        st.session_state.confirm_delete_id = None
        st.rerun()
        
    with confirmation_placeholder.container():
        st.error(f"⚠️ **KONFIRMASI PENGHAPUSAN**")
        st.warning(f"Anda yakin ingin menghapus laporan ID **ID{delete_id}**?")
        
        st.info(f"**Detail:** {masalah} ({unit})")
        
        col_yes, col_no = st.columns([1, 4])
        
        if col_yes.button("🗑️ Ya, Hapus Permanen", key="confirm_yes"):
            delete_data(delete_id) 
        
        if col_no.button("❌ Batal", key="confirm_no"):
            st.session_state.confirm_delete_id = None
            st.rerun()

# =========================================================
# === TOMBOL INPUT & FORMULIR ===
# =========================================================
    
st.write("")
if st.button("➕ Tambah Laporan Kerusakan Baru", use_container_width=True):
    st.session_state.show_new_report_form_v2 = not st.session_state.show_new_report_form_v2

if st.session_state.get('show_new_report_form_v2'):
    st.subheader("Formulir Laporan Baru")
    
    with st.form("new_report_form_v2", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        vessel_options_new = [SELECTED_SHIP_CODE] 
        
        with col1:
            st.markdown("<h5 style='color:#005691;'>Informasi Dasar</h5>", unsafe_allow_html=True)
            vessel_select = st.selectbox("Nama Kapal (Vessel)*", 
                                         options=vessel_options_new, 
                                         key="vessel_select_new",
                                         index=0,
                                         disabled=True)
            vessel = vessel_select 
                
            unit_select = st.selectbox("Unit/Sistem yang Rusak", options=[''] + unit_options + ['--- Input Baru ---'], key="unit_select") 
            if unit_select == '--- Input Baru ---' or unit_select == '':
                unit = st.text_input("Unit (Input Manual)", key="unit_manual").upper().strip()
            else:
                unit = unit_select
                
            day = st.date_input("Tanggal Kejadian (Day)*", datetime.now().date(), key="day_input")
        
        with col2:
            st.markdown("<h5 style='color:#005691;'>Detail Laporan & Status</h5>", unsafe_allow_html=True)
            permasalahan = st.text_area("Detail Permasalahan*", height=100)
            penyelesaian = st.text_area("Langkah Penyelesaian Sementara/Tindakan")
            keterangan = st.text_input("Keterangan Tambahan")
            
            status_cols = st.columns(2)
            with status_cols[0]:
                default_status = st.selectbox("Status Awal Laporan", options=['OPEN', 'CLOSED'], index=0) 
            
            with status_cols[1]:
                closed_date_input = st.date_input("Tanggal Selesai (Jika Closed)", 
                                                 value=None, 
                                                 disabled=(default_status == 'OPEN'),
                                                 key='closed_date_input_new')

        submitted_new = st.form_submit_button("✅ Simpan Laporan")
        
        if submitted_new:
            final_vessel = vessel.upper().strip()
            final_unit = unit.upper().strip()
            
            if not final_vessel or not permasalahan:
                st.error("Nama Kapal dan Permasalahan wajib diisi.")
                st.stop()
            
            closed_date_val = ""
            if default_status == 'CLOSED' and closed_date_input is not None:
                closed_date_val = closed_date_input.strftime(DATE_FORMAT)
                
            issued_date_val = day.strftime(DATE_FORMAT)
            
            new_row = {
                'Day': issued_date_val, 
                'Vessel': final_vessel, 
                'Permasalahan': permasalahan,
                'Penyelesaian': penyelesaian,
                'Unit': final_unit,
                'Issued Date': issued_date_val, 
                'Closed Date': closed_date_val, 
                'Keterangan': keterangan,
                'Status': default_status.upper() 
            }
            
            if add_new_data(new_row):
                st.session_state.show_new_report_form_v2 = False 
                time.sleep(1) 
                st.rerun() 

st.markdown("---")

# =========================================================
# === TAMPILAN DATA RIWAYAT (CLOSED) ===
# =========================================================

with st.expander("📁 Lihat Riwayat Laporan (CLOSED)"):
    df_closed = df_filtered_ship[df_filtered_ship['status'].str.upper() == 'CLOSED'].copy()

    if selected_year and selected_year != 'All':
          df_closed = df_closed[df_closed['Date_Day'].dt.year == int(selected_year)]

    if df_closed.empty:
        st.info("Belum ada laporan yang berstatus CLOSED untuk kapal ini.")
    else:
        st.caption("Klik dua kali pada sel di tabel untuk **Edit Inline**. Tanggal harus dalam format **DD/MM/YYYY**.")

        df_closed_display = df_closed.copy()
        df_closed_display.insert(0, 'ID Laporan', df_closed_display['id'].apply(lambda x: f"ID{x}"))

        editable_columns_closed = {
            'ID Laporan': st.column_config.Column("ID Laporan", disabled=True),
            'day': st.column_config.TextColumn("Day (DD/MM/YYYY)", required=True),
            'vessel': st.column_config.TextColumn("Vessel", disabled=True),
            'unit': st.column_config.SelectboxColumn("Unit", options=unit_options, required=True, help="Pilih dari daftar unit yang sudah ada."),
            'issued_date': st.column_config.TextColumn("Issued Date", disabled=True), 
            'closed_date': st.column_config.TextColumn("Closed Date (DD/MM/YYYY)"), 
            'status': st.column_config.SelectboxColumn("Status", options=['OPEN', 'CLOSED'], required=True)
        }
        
        # Define column order for display
        display_columns = ['ID Laporan', 'day', 'vessel', 'permasalahan', 'penyelesaian', 'unit', 
                          'issued_date', 'closed_date', 'keterangan', 'status']
        
        edited_df_closed = st.data_editor(
            df_closed_display[display_columns],
            column_config=editable_columns_closed,
            hide_index=True,
            use_container_width=True,
            key='closed_report_editor' 
        )
        
        if not df_closed_display[display_columns].equals(edited_df_closed):
            st.warning("⚠️ Perubahan riwayat terdeteksi. Silakan klik tombol 'Simpan Perubahan Riwayat' untuk menyimpan data.")
            
            col_save, col_spacer_save = st.columns([1, 5])
            with col_save:
                if st.button("💾 Simpan Perubahan Riwayat", key='save_button_closed'):
                    
                    has_error = False

                    for index, edited_row in edited_df_closed.iterrows():
                        
                        unique_id_str = edited_row['ID Laporan']
                        unique_id = int(unique_id_str.replace('ID', ''))  # Extract ID from "IDxxx"

                        closed_date_val = str(edited_row['closed_date']).strip()
                        current_status = edited_row['status'].upper().strip()
                        
                        updated_data = {
                            'Day': str(edited_row['day']).strip(),
                            'Vessel': SELECTED_SHIP_CODE,
                            'Permasalahan': str(edited_row['permasalahan']),
                            'Penyelesaian': str(edited_row['penyelesaian']),
                            'Unit': str(edited_row['unit']).upper(),
                            'Issued Date': str(edited_row['issued_date']).strip(),
                            'Closed Date': closed_date_val,
                            'Keterangan': str(edited_row['keterangan']),
                            'Status': current_status
                        }

                        # 1. Validasi Tanggal
                        try:
                            datetime.strptime(updated_data['Day'], DATE_FORMAT)
                        except ValueError:
                            st.error(f"Baris ID {unique_id_str}: Format Tanggal Kejadian (Day) salah. Gunakan DD/MM/YYYY.")
                            has_error = True
                            
                        if current_status == 'CLOSED' and closed_date_val and closed_date_val != '':
                            try:
                                datetime.strptime(closed_date_val, DATE_FORMAT)
                            except ValueError:
                                st.error(f"Baris ID {unique_id_str}: Format Tanggal Selesai (Closed Date) salah. Gunakan DD/MM/YYYY.")
                                has_error = True
                            
                    if has_error:
                        st.stop()
                    
                    # Apply all updates
                    success_count = 0
                    for index, edited_row in edited_df_closed.iterrows():
                        unique_id_str = edited_row['ID Laporan']
                        unique_id = int(unique_id_str.replace('ID', ''))
                        
                        updated_data = {
                            'Day': str(edited_row['day']).strip(),
                            'Vessel': SELECTED_SHIP_CODE,
                            'Permasalahan': str(edited_row['permasalahan']),
                            'Penyelesaian': str(edited_row['penyelesaian']),
                            'Unit': str(edited_row['unit']).upper(),
                            'Issued Date': str(edited_row['issued_date']).strip(),
                            'Closed Date': str(edited_row['closed_date']).strip(),
                            'Keterangan': str(edited_row['keterangan']),
                            'Status': str(edited_row['status']).upper()
                        }
                        
                        try:
                            db.update_laporan(unique_id, updated_data)
                            success_count += 1
                        except Exception as e:
                            st.error(f"Gagal update ID {unique_id}: {e}")
                    
                    st.success(f"✅ {success_count} laporan berhasil diupdate!")
                    time.sleep(2)
                    st.rerun()