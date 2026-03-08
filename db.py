import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',              # ← your MySQL username
    'password': 'nnrg',  # ← your MySQL password
    'database': 'student_grade_system'     # ← your database name
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def execute_query(query, params=None, fetch=True):
    conn = get_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        return result
    except Error as e:
        print(f"[QUERY ERROR] {e}")
        return None
    finally:
        cursor.close()
        conn.close()