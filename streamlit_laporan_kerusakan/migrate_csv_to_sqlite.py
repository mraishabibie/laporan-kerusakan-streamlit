import pandas as pd
import streamlit as st
from database import db
import os

def migrate_csv_to_sqlite_app():
    st.title("🔄 Migrasi Data CSV ke SQLite")
    st.write("Tool untuk memindahkan data existing dari CSV ke database SQLite")
    
    uploaded_file = st.file_uploader("Upload file CSV existing", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Read CSV file
            df = pd.read_csv(uploaded_file)
            
            st.subheader("Preview Data CSV")
            st.write(f"Total baris: {len(df)}")
            st.write("Kolom yang terdeteksi:")
            st.write(df.columns.tolist())
            st.dataframe(df.head(5))
            
            if st.button("🚀 Mulai Migrasi ke SQLite"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                success_count = 0
                error_count = 0
                errors = []
                
                for i, row in df.iterrows():
                    try:
                        # Map CSV columns to database fields
                        data = {
                            'Day': str(row.get('Day', '')),
                            'Vessel': str(row.get('Vessel', '')).upper().strip(),
                            'Permasalahan': str(row.get('Permasalahan', '')),
                            'Penyelesaian': str(row.get('Penyelesaian', '')),
                            'Unit': str(row.get('Unit', '')).upper().strip(),
                            'Issued Date': str(row.get('Issued Date', '')),
                            'Closed Date': str(row.get('Closed Date', '')),
                            'Keterangan': str(row.get('Keterangan', '')),
                            'Status': str(row.get('Status', 'OPEN')).upper().strip()
                        }
                        
                        # Insert to database
                        db.add_laporan(data)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Baris {i+1}: {str(e)}")
                    
                    # Update progress
                    progress = (i + 1) / len(df)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing... {i+1}/{len(df)}")
                
                st.success(f"✅ Migrasi selesai!")
                st.info(f"**Berhasil:** {success_count} baris")
                st.info(f"**Gagal:** {error_count} baris")
                
                if errors:
                    with st.expander("Detail Error:"):
                        for error in errors[:10]:  # Show first 10 errors
                            st.error(error)
                
                # Show migrated data
                all_data = db.get_all_laporan()
                st.subheader("Data di Database Setelah Migrasi")
                st.write(f"Total records: {len(all_data)}")
                
                # Show summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Vessels", all_data['vessel'].nunique())
                with col2:
                    st.metric("Open Reports", (all_data['status'] == 'OPEN').sum())
                with col3:
                    st.metric("Closed Reports", (all_data['status'] == 'CLOSED').sum())
                
                st.dataframe(all_data[['id', 'vessel', 'unit', 'status', 'created_at']].head(10))
                
        except Exception as e:
            st.error(f"Error membaca file: {e}")

if __name__ == "__main__":
    migrate_csv_to_sqlite_app()