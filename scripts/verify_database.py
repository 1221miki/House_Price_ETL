import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from config.database import get_db_connection, test_connection

def verify_tables(conn):
    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION: TABLES & ROW COUNTS")
    print("=" * 60)
    
    tables = ["properties", "sale_events"]
    with conn.cursor() as cur:
        for tbl in tables:
            # Check table existence
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                );
            """, (tbl,))
            exists = cur.fetchone()[0]
            
            if exists:
                cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                count = cur.fetchone()[0]
                print(f"  [OK] Table '{tbl}': {count:,} rows")
            else:
                print(f"  [MISSING] Table '{tbl}' does not exist.")

def verify_indexes(conn):
    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION: PERFORMANCE INDEXES")
    print("=" * 60)
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT tablename, indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            ORDER BY tablename, indexname;
        """)
        indexes = cur.fetchall()
        if indexes:
            for tbl, idx in indexes:
                print(f"  - Table '{tbl}': Index '{idx}'")
        else:
            print("  [WARNING] No custom indexes found.")

def verify_views(conn):
    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION: ANALYTICAL VIEWS")
    print("=" * 60)
    
    views = [
        "v_market_summary_by_borough_year",
        "v_assessment_vs_market_price",
        "v_property_type_performance",
        "v_top_appreciated_zip_codes"
    ]
    with conn.cursor() as cur:
        for vw in views:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.views 
                    WHERE table_schema = 'public' AND table_name = %s
                );
            """, (vw,))
            exists = cur.fetchone()[0]
            status = "[OK] Active" if exists else "[MISSING]"
            print(f"  {status} View: '{vw}'")

def main():
    print("Connecting to PostgreSQL database...")
    if not test_connection():
        print("[ERROR] Could not connect to PostgreSQL. Please check database server and credentials in .env")
        return
        
    conn = get_db_connection()
    try:
        verify_tables(conn)
        verify_indexes(conn)
        verify_views(conn)
        print("\n" + "=" * 60)
        print("DATABASE INTEGRITY CHECK COMPLETE")
        print("=" * 60)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
