import psycopg2
from contextlib import contextmanager
from .config import get_db_config, DB_SCHEMA

@contextmanager
def get_db_connection():
    cfg = get_db_config()
    conn = None
    try:
        conn = psycopg2.connect(
            host=cfg["host"],
            database=cfg["database"],
            user=cfg["user"],
            password=cfg["password"],
            port=cfg["port"],
            sslmode=cfg.get("sslmode", "require"),
            connect_timeout=10,
        )
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute("SET TIME ZONE 'America/Fortaleza'")
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {DB_SCHEMA}")
            cur.execute(f"SET search_path TO {DB_SCHEMA}, public")
        yield conn
    finally:
        if conn:
            conn.close()

def test_db_connection():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_schema(), version();")
                schema, ver = cur.fetchone()
                return True, f"✅ Conectado. Schema atual: {schema}. {ver}"
    except Exception as e:
        return False, f"❌ Falha na conexão: {str(e)}"
