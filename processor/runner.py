import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "patients.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# check if column already exists
cursor.execute("PRAGMA table_info(patients)")
columns = [col[1] for col in cursor.fetchall()]

if "report_json" not in columns:

    cursor.execute("""
        ALTER TABLE patients
        ADD COLUMN report_json TEXT
    """)

    print("report_json column added successfully")

else:
    print("report_json column already exists")

conn.commit()
conn.close()