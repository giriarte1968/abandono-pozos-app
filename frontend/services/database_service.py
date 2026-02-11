import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseService:
    """Servicio para interactuar con la base de datos MySQL de forma síncrona."""
    
    def __init__(self):
        # En desarrollo local usamos localhost (vía .env), en contenedor usamos el host del env
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("MYSQL_PORT", 3306))
        self.user = os.getenv("MYSQL_USER", "pna_user")
        self.password = os.getenv("MYSQL_PASSWORD", "pna_pass")
        self.db_name = os.getenv("MYSQL_DATABASE", "pna_system")

    def _get_connection(self):
        try:
            return pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.db_name,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True,
                connect_timeout=2 # Quick fail
            )
        except Exception:
            return None

    def is_available(self):
        conn = self._get_connection()
        if conn:
            conn.close()
            return True
        return False

    def fetch_all(self, query, params=None):
        conn = self._get_connection()
        if not conn:
            return []
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            conn.close()

    def fetch_one(self, query, params=None):
        conn = self._get_connection()
        if not conn:
            return None
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        finally:
            conn.close()

    def execute(self, query, params=None):
        conn = self._get_connection()
        if not conn:
            return 0
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
        finally:
            conn.close()
