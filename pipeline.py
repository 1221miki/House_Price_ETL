import os
import sys
import time
import argparse
from datetime import datetime

from config.database import get_db_connection, test_connection, ensure_database_exists
from etl.extract import extract_parquet_chunks, get_parquet_row_count
from etl.transform import transform_properties, transform_sales
from etl.load import bulk_load_dataframe

# Paths to data files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
PROPERTIES_FILE = os.path.join(DATA_DIR, "properties-00000-of-00001.parquet")
SALES_FILE = os.path.join(DATA_DIR, "sale_events-00000-of-00001.parquet")
SCHEMA_FILE = os.path.join(BASE_DIR, "sql", "schema.sql")
VIEWS_FILE = os.path.join(BASE_DIR, "sql", "analytical_views.sql")

def execute_sql_file(conn, file_path: str, description: str):
    """Executes a SQL file containing multiple statements."""
    if not os.path.exists(file_path):
        print(f"[ERROR] SQL file not found: {file_path}")
        return False
        
    print(f"\n[Database DDL] Executing {description} from {os.path.basename(file_path)}...")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
        
    with conn.cursor() as cur:
        cur.execute(sql_content)
    conn.commit()
    print(f"[Database DDL] {description} executed successfully.")
    return True

def run_properties_pipeline(conn, batch_size: int, limit: int = None):
    """Extracts, transforms, and loads the properties dataset."""
    print("\n" + "=" * 60)
    print("STARTING PROPERTIES ETL PIPELINE")
    print("=" * 60)
    
    if not os.path.exists(PROPERTIES_FILE):
        print(f"[ERROR] Missing file: {PROPERTIES_FILE}")
        return 0
        
    total_file_rows = get_parquet_row_count(PROPERTIES_FILE)
    target_rows = min(total_file_rows, limit) if limit else total_file_rows
    print(f"Dataset: NYC PLUTO Properties (~{total_file_rows:,} total rows in Parquet)")
    print(f"Targeting: {target_rows:,} rows with batch size {batch_size:,}")
    
    start_time = time.time()
    total_loaded = 0
    batch_num = 0
    
    for raw_chunk in extract_parquet_chunks(PROPERTIES_FILE, chunk_size=batch_size, max_records=limit):
        batch_num += 1
        b_start = time.time()
        
        # Transform
        transformed_df = transform_properties(raw_chunk)
        
        # Load
        loaded_count = bulk_load_dataframe(
            df=transformed_df,
            table_name="properties",
            conn=conn,
            primary_key="record_id",
            use_staging_dedup=True
        )
        
        total_loaded += loaded_count
        b_elapsed = time.time() - b_start
        throughput = loaded_count / b_elapsed if b_elapsed > 0 else 0
        
        pct = (total_loaded / target_rows) * 100 if target_rows else 0
        print(f"  [Batch {batch_num:03d}] Loaded {loaded_count:,} rows in {b_elapsed:.2f}s "
              f"({throughput:,.0f} rows/s) | Progress: {total_loaded:,}/{target_rows:,} ({pct:.1f}%)")
              
    total_elapsed = time.time() - start_time
    avg_throughput = total_loaded / total_elapsed if total_elapsed > 0 else 0
    print(f"[PROPERTIES COMPLETE] Loaded {total_loaded:,} properties in {total_elapsed:.1f}s "
          f"(Avg: {avg_throughput:,.0f} rows/s)")
    return total_loaded

def run_sales_pipeline(conn, batch_size: int, limit: int = None):
    """Extracts, transforms, and loads the sales events dataset."""
    print("\n" + "=" * 60)
    print("STARTING SALE EVENTS ETL PIPELINE")
    print("=" * 60)
    
    if not os.path.exists(SALES_FILE):
        print(f"[ERROR] Missing file: {SALES_FILE}")
        return 0
        
    total_file_rows = get_parquet_row_count(SALES_FILE)
    target_rows = min(total_file_rows, limit) if limit else total_file_rows
    print(f"Dataset: NYC Historical Sale Events (~{total_file_rows:,} total rows in Parquet)")
    print(f"Targeting: {target_rows:,} rows with batch size {batch_size:,}")
    
    start_time = time.time()
    total_loaded = 0
    batch_num = 0
    
    for raw_chunk in extract_parquet_chunks(SALES_FILE, chunk_size=batch_size, max_records=limit):
        batch_num += 1
        b_start = time.time()
        
        # Transform
        transformed_df = transform_sales(raw_chunk)
        
        # Load
        loaded_count = bulk_load_dataframe(
            df=transformed_df,
            table_name="sale_events",
            conn=conn,
            primary_key="sale_id",
            use_staging_dedup=True
        )
        
        total_loaded += loaded_count
        b_elapsed = time.time() - b_start
        throughput = loaded_count / b_elapsed if b_elapsed > 0 else 0
        
        pct = (total_loaded / target_rows) * 100 if target_rows else 0
        print(f"  [Batch {batch_num:03d}] Loaded {loaded_count:,} rows in {b_elapsed:.2f}s "
              f"({throughput:,.0f} rows/s) | Progress: {total_loaded:,}/{target_rows:,} ({pct:.1f}%)")
              
    total_elapsed = time.time() - start_time
    avg_throughput = total_loaded / total_elapsed if total_elapsed > 0 else 0
    print(f"[SALES COMPLETE] Loaded {total_loaded:,} sales in {total_elapsed:.1f}s "
          f"(Avg: {avg_throughput:,.0f} rows/s)")
    return total_loaded

def verify_database_counts(conn):
    """Queries and prints current row counts in PostgreSQL tables."""
    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION SUMMARY")
    print("=" * 60)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM properties;")
        prop_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM sale_events;")
        sale_count = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(DISTINCT s.parcel_id)
            FROM sale_events s
            INNER JOIN properties p ON s.parcel_id = p.parcel_id;
        """)
        linked_parcels = cur.fetchone()[0]
        
    print(f"  * Total Properties in DB : {prop_count:,}")
    print(f"  * Total Sale Events in DB: {sale_count:,}")
    print(f"  * Total Combined Records : {prop_count + sale_count:,}")
    print(f"  * Linked Properties/Sales: {linked_parcels:,} distinct parcels")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="NYC Real Estate Data Pipeline & ETL Orchestrator")
    parser.add_argument("--init-db", action="store_true", help="Initialize or reset database tables and indexes")
    parser.add_argument("--apply-views", action="store_true", default=True, help="Create analytical views")
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("BATCH_SIZE", 50000)), help="Rows per batch")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to process per dataset (optional)")
    parser.add_argument("--skip-properties", action="store_true", help="Skip loading properties table")
    parser.add_argument("--skip-sales", action="store_true", help="Skip loading sales table")
    
    args = parser.parse_args()
    
    env_limit = os.getenv("MAX_RECORDS")
    if args.limit is None and env_limit and env_limit.strip():
        args.limit = int(env_limit.strip())
        
    print("=" * 60)
    print("NYC REAL ESTATE ETL DATA PIPELINE")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Batch Size: {args.batch_size:,} | Limit: {f'{args.limit:,}' if args.limit else 'FULL DATASET'}")
    print("=" * 60)
    
    # 1. Test connection
    if not test_connection():
        print("\nDatabase is not reachable. Attempting to ensure database exists...")
        if not ensure_database_exists():
            print("\nPlease check your PostgreSQL service or edit your .env file.")
            sys.exit(1)
            
    conn = get_db_connection()
    
    try:
        # 2. Schema initialization
        if args.init_db:
            execute_sql_file(conn, SCHEMA_FILE, "Tables and Indexes Schema")
            
        # 3. Properties pipeline
        if not args.skip_properties:
            run_properties_pipeline(conn, batch_size=args.batch_size, limit=args.limit)
            
        # 4. Sales pipeline
        if not args.skip_sales:
            run_sales_pipeline(conn, batch_size=args.batch_size, limit=args.limit)
            
        # 5. Apply Analytical Views
        if args.apply_views:
            execute_sql_file(conn, VIEWS_FILE, "Analytical Business Intelligence Views")
            
        # 6. Verification
        verify_database_counts(conn)
        print("\nETL PIPELINE COMPLETED SUCCESSFULLY!")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
