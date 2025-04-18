# SQLite setup for doctors and patients
# backend/db.py
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
import string

DB_PATH = Path("chat_history.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS doctors (id TEXT PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS patients (id TEXT, doctor_id TEXT, PRIMARY KEY (id, doctor_id))")
    cur.execute("CREATE TABLE IF NOT EXISTS chats (doctor_id TEXT, patient_id TEXT, message TEXT, is_user INTEGER)")
    conn.commit()
    conn.close()

def get_patients(doctor_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id FROM patients WHERE doctor_id=?", (doctor_id,))
    results = [row[0] for row in cur.fetchall()]
    conn.close()
    return results

def add_patient(doctor_id, patient_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO doctors (id) VALUES (?)", (doctor_id,))
    cur.execute("INSERT OR IGNORE INTO patients (id, doctor_id) VALUES (?, ?)", (patient_id, doctor_id))
    conn.commit()
    conn.close()

def save_chat(doctor_id, patient_id, message, is_user):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO chats VALUES (?, ?, ?, ?)", (doctor_id, patient_id, message, is_user))
    conn.commit()
    conn.close()

def get_chat_history(doctor_id, patient_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT message, is_user FROM chats WHERE doctor_id=? AND patient_id=?", (doctor_id, patient_id))
    rows = cur.fetchall()
    conn.close()
    return rows


class Database:
    def __init__(self, db_name="homeo.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            email TEXT PRIMARY KEY,
            name TEXT,
            mobile TEXT,
            reg_number TEXT,
            is_verified INTEGER DEFAULT 0,
            otp TEXT,
            otp_expiry TEXT,
            last_query_date TEXT,
            daily_query_count INTEGER DEFAULT 0,
            total_queries INTEGER DEFAULT 0
        )
        ''')
        self.conn.commit()

    def generate_otp(self):
        return ''.join(random.choices(string.digits, k=6))

    def get_doctor(self, email):
        self.cursor.execute("SELECT * FROM doctors WHERE email=?", (email,))
        return self.cursor.fetchone()

    def register_doctor(self, email, name, mobile, reg_number):
        otp = self.generate_otp()
        expiry = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        self.cursor.execute(
            "INSERT INTO doctors (email, name, mobile, reg_number, otp, otp_expiry) VALUES (?, ?, ?, ?, ?, ?)",
            (email, name, mobile, reg_number, otp, expiry)
        )
        self.conn.commit()
        return otp

    def verify_otp(self, email, otp):
        self.cursor.execute("SELECT otp, otp_expiry FROM doctors WHERE email=?", (email,))
        row = self.cursor.fetchone()
        if not row:
            return None
        stored_otp, expiry = row
        if otp != stored_otp:
            return False
        if datetime.utcnow() > datetime.fromisoformat(expiry):
            return False
        
        self.cursor.execute("UPDATE doctors SET is_verified=1 WHERE email=?", (email,))
        self.conn.commit()
        return True

    def update_query_count(self, email, daily_count, total_count, today):
        self.cursor.execute(
            "UPDATE doctors SET last_query_date=?, daily_query_count=?, total_queries=? WHERE email=?",
            (today, daily_count, total_count, email)
        )
        self.conn.commit()