import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "house_price_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_SSLMODE = os.getenv("DB_SSLMODE", "prefer")

def get_connection_params():
    """Return dictionary of connection parameters."""
    params = {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }
    if DB_SSLMODE:
        params["sslmode"] = DB_SSLMODE
    return params

def get_db_connection():
    """Create and return a raw psycopg2 connection (supports Neon cloud & local)."""
    if DATABASE_URL:
        # Handles connection string format from Neon (postgresql://...)
        conn_str = DATABASE_URL
        if conn_str.startswith("postgresql://") and "sslmode" not in conn_str:
            separator = "&" if "?" in conn_str else "?"
            conn_str = f"{conn_str}{separator}sslmode=require"
        return psycopg2.connect(conn_str)
    else:
        params = get_connection_params()
        return psycopg2.connect(**params)

from urllib.parse import quote_plus

def get_db_engine():
    """Create and return a SQLAlchemy engine."""
    if DATABASE_URL:
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return create_engine(url)
    else:
        encoded_pass = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
        url = f"postgresql+psycopg2://{DB_USER}:{encoded_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        return create_engine(url)

def ensure_database_exists():
    """
    Connects to the default 'postgres' database and creates the target database
    if it does not already exist (for local instances).
    """
    if DATABASE_URL:
        # Cloud providers like Neon manage database creation in their web console
        return True
        
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f"CREATE DATABASE \"{DB_NAME}\"")
            print(f"[Database Setup] Created database '{DB_NAME}' successfully.")
        else:
            print(f"[Database Setup] Database '{DB_NAME}' already exists.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[Database Setup Warning] Could not verify/create database: {e}")
        return False

def test_connection():
    """Test if PostgreSQL database is reachable."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            ver = cur.fetchone()[0]
            print(f"[Database Connected] {ver.split(',')[0]}")
        conn.close()
        return True
    except Exception as e:
        print(f"[Connection Error] {e}")
        return False

if __name__ == "__main__":
    test_connection()
