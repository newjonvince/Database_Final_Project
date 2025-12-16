import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "192.168.1.36",
    "port": 3306,
    "user": "jon",
    "password": "Jhonnyv1129!",
    "database": "final_project_db",
}

def get_connection():
    """Establish and return a MySQL database connection."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise RuntimeError(f"MySQL connection error: {e}")
