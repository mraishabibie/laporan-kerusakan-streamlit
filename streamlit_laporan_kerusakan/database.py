import sqlite3
import pandas as pd
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='data/laporan_kerusakan.db'):
        self.db_path = db_path
        self._ensure_data_dir()
        self.init_db()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs('data', exist_ok=True)
    
    def init_db(self):
        """Initialize database dengan schema yang benar"""
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS laporan_kerusakan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT,
                vessel TEXT NOT NULL,
                permasalahan TEXT NOT NULL,
                penyelesaian TEXT,
                unit TEXT,
                issued_date TEXT,
                closed_date TEXT,
                keterangan TEXT,
                status TEXT DEFAULT 'OPEN',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index untuk performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_vessel ON laporan_kerusakan(vessel)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_status ON laporan_kerusakan(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_unit ON laporan_kerusakan(unit)')
        
        conn.commit()
        conn.close()
        # print(f"✅ Database initialized at: {self.db_path}")
    
    def get_connection(self):
        # Render.com bisa pakai thread berbeda
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    # CRUD Operations
    def get_all_laporan(self):
        """Get semua laporan"""
        conn = self.get_connection()
        try:
            df = pd.read_sql('''
                SELECT * FROM laporan_kerusakan 
                ORDER BY 
                    CASE WHEN status = 'OPEN' THEN 1 ELSE 2 END,
                    created_at DESC
            ''', conn)
            return df
        finally:
            conn.close()
    
    def get_laporan_by_vessel(self, vessel):
        """Get laporan by vessel"""
        conn = self.get_connection()
        try:
            df = pd.read_sql('''
                SELECT * FROM laporan_kerusakan 
                WHERE vessel = ? 
                ORDER BY 
                    CASE WHEN status = 'OPEN' THEN 1 ELSE 2 END,
                    created_at DESC
            ''', conn, params=[vessel.upper()])
            return df
        finally:
            conn.close()
    
    def add_laporan(self, data):
        """Tambah laporan baru"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO laporan_kerusakan 
                (day, vessel, permasalahan, penyelesaian, unit, issued_date, closed_date, keterangan, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('Day', ''),
                data.get('Vessel', '').upper(),
                data.get('Permasalahan', ''),
                data.get('Penyelesaian', ''),
                data.get('Unit', ''),
                data.get('Issued Date', ''),
                data.get('Closed Date', ''),
                data.get('Keterangan', ''),
                data.get('Status', 'OPEN')
            ))
            conn.commit()
            return c.lastrowid
        finally:
            conn.close()
    
    def update_laporan(self, laporan_id, data):
        """Update laporan existing"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('''
                UPDATE laporan_kerusakan 
                SET day=?, vessel=?, permasalahan=?, penyelesaian=?, unit=?, 
                    issued_date=?, closed_date=?, keterangan=?, status=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (
                data.get('Day', ''),
                data.get('Vessel', '').upper(),
                data.get('Permasalahan', ''),
                data.get('Penyelesaian', ''),
                data.get('Unit', ''),
                data.get('Issued Date', ''),
                data.get('Closed Date', ''),
                data.get('Keterangan', ''),
                data.get('Status', 'OPEN'),
                laporan_id
            ))
            conn.commit()
            return True
        finally:
            conn.close()
    
    def delete_laporan(self, laporan_id):
        """Hapus laporan"""
        conn = self.get_connection()
        c = conn.cursor()
        try:
            c.execute('DELETE FROM laporan_kerusakan WHERE id = ?', (laporan_id,))
            conn.commit()
            return True
        finally:
            conn.close()
    
    def get_stats(self):
        """Get statistics untuk dashboard"""
        conn = self.get_connection()
        try:
            query = '''
                SELECT 
                    vessel,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_count,
                    SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed_count,
                    MAX(created_at) as last_activity
                FROM laporan_kerusakan 
                GROUP BY vessel
                ORDER BY vessel
            '''
            return pd.read_sql(query, conn)
        finally:
            conn.close()
    
    def get_dashboard_data(self):
        """Get data khusus untuk dashboard analytics"""
        conn = self.get_connection()
        try:
            return pd.read_sql('''
                SELECT 
                    id, day, vessel, permasalahan, penyelesaian, unit,
                    issued_date, closed_date, keterangan, status, created_at
                FROM laporan_kerusakan 
                ORDER BY created_at DESC
            ''', conn)
        finally:
            conn.close()

# Global instance
db = DatabaseManager()
