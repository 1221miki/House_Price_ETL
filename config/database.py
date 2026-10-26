import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "house_price_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def get_connection_params():
    """Return dictionary of connection parameters."""
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }

def get_db_connection():
    """Create and return a raw psycopg2 connection."""
    params = get_connection_params()
    return psycopg2.connect(**params)

def get_db_engine():
    """Create and return a SQLAlchemy engine."""
    url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)

def ensure_database_exists():
    """
    Connects to the default 'postgres' database and creates the target database
    if it does not already exist.
    """
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
        print(f"[Database Setup Error] Could not verify/create database: {e}")
        return False

def test_connection():
    """Test connection to the PostgreSQL database."""
    print("Testing connection to PostgreSQL...")
    print(f"Host: {DB_HOST}:{DB_PORT} | Database: {DB_NAME} | User: {DB_USER}")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(f"SUCCESS: Connected to PostgreSQL!\nVersion: {version}")
        return True
    except Exception as e:
        print(f"FAILED: Connection failed.\nError: {e}")
        print("\nTroubleshooting tips:")
        print("1. Ensure PostgreSQL is running on host and port specified in .env.")
        print(f"2. Ensure the database '{DB_NAME}' exists or run ensure_database_exists().")
        print("3. Verify username and password in .env.")
        return False

if __name__ == "__main__":
    test_connection()
