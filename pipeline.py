import os
import sys
import time
import logging
import argparse
import tracemalloc
from datetime import datetime
from pathlib import Path

from config.database import get_db_connection, test_connection, ensure_database_exists
from etl.extract import extract_parquet_chunks, get_parquet_row_count
from etl.transform import transform_properties, transform_sales
from etl.validate import validate_properties, validate_sales
from etl.load import bulk_load_dataframe

# Base paths
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging
log_file = LOGS_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ETL_Pipeline")

def find_data_file(filename: str, use_sample: bool = False) -> Path:
    """Finds a dataset file in candidate locations across data/samples, data/raw, data, or Data."""
    if use_sample:
        sample_name = "properties_sample.parquet" if "properties" in filename else "sale_events_sample.parquet"
        sample_cand = BASE_DIR / "data" / "samples" / sample_name
        if sample_cand.exists():
            return sample_cand

    candidates = [
        BASE_DIR / "data" / "raw" / filename,
        BASE_DIR / "Data" / "raw" / filename,
        BASE_DIR / "data" / filename,
        BASE_DIR / "Data" / filename,
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]

SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"
VIEWS_FILE = BASE_DIR / "sql" / "analytical_views.sql"

def execute_sql_file(conn, file_path: Path, description: str):
    """Executes a SQL file containing multiple statements."""
    if not file_path.exists():
        logger.error(f"SQL file not found: {file_path}")
        return False
        
    logger.info(f"[Database DDL] Executing {description} from {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()
        
    with conn.cursor() as cur:
        cur.execute(sql_content)
    conn.commit()
    logger.info(f"[Database DDL] {description} executed successfully.")
    return True

def run_properties_pipeline(conn, prop_file: Path, batch_size: int, limit: int = None):
    """Extracts, transforms, validates, and loads the properties dataset."""
    logger.info("=" * 60)
    logger.info("STARTING PROPERTIES ETL PIPELINE")
    logger.info("=" * 60)
    
    if not prop_file.exists():
        logger.error(f"Missing file: {prop_file}")
        return 0
        
    total_file_rows = get_parquet_row_count(str(prop_file))
    target_rows = min(total_file_rows, limit) if limit else total_file_rows
    logger.info(f"Dataset: NYC PLUTO Properties (~{total_file_rows:,} total rows in Parquet)")
    logger.info(f"Source file: {prop_file.relative_to(BASE_DIR)}")
    logger.info(f"Targeting: {target_rows:,} rows with batch size {batch_size:,}")
    
    start_time = time.time()
    total_loaded = 0
    total_rejected = 0
    batch_num = 0
    
    for raw_chunk in extract_parquet_chunks(str(prop_file), chunk_size=batch_size, max_records=limit):
        batch_num += 1
        b_start = time.time()
        
        # 1. Transform
        transformed_df = transform_properties(raw_chunk)
        
        # 2. Validate
        validated_df, metrics = validate_properties(transformed_df)
        total_rejected += metrics["rejected_records"]
        
        # 3. Load
        loaded_count = bulk_load_dataframe(
            df=validated_df,
            table_name="properties",
            conn=conn,
            primary_key="record_id",
            use_staging_dedup=True
        )
        
        total_loaded += loaded_count
        b_elapsed = time.time() - b_start
        throughput = loaded_count / b_elapsed if b_elapsed > 0 else 0
        
        pct = (total_loaded / target_rows) * 100 if target_rows else 0
        logger.info(
            f"  [Batch {batch_num:03d}] Validated {len(validated_df):,} | Loaded {loaded_count:,} rows in {b_elapsed:.2f}s "
            f"({throughput:,.0f} rows/s) | Progress: {total_loaded:,}/{target_rows:,} ({pct:.1f}%)"
        )
              
    total_elapsed = time.time() - start_time
    avg_throughput = total_loaded / total_elapsed if total_elapsed > 0 else 0
    logger.info(
        f"[PROPERTIES COMPLETE] Loaded {total_loaded:,} properties (Rejected {total_rejected:,}) in {total_elapsed:.1f}s "
        f"(Avg: {avg_throughput:,.0f} rows/s)"
    )
    return total_loaded

def run_sales_pipeline(conn, sales_file: Path, batch_size: int, limit: int = None):
    """Extracts, transforms, validates, and loads the sales events dataset."""
    logger.info("=" * 60)
    logger.info("STARTING SALE EVENTS ETL PIPELINE")
    logger.info("=" * 60)
    
    if not sales_file.exists():
        logger.error(f"Missing file: {sales_file}")
        return 0
        
    total_file_rows = get_parquet_row_count(str(sales_file))
    target_rows = min(total_file_rows, limit) if limit else total_file_rows
    logger.info(f"Dataset: NYC Historical Sale Events (~{total_file_rows:,} total rows in Parquet)")
    logger.info(f"Source file: {sales_file.relative_to(BASE_DIR)}")
    logger.info(f"Targeting: {target_rows:,} rows with batch size {batch_size:,}")
    
    start_time = time.time()
    total_loaded = 0
    total_rejected = 0
    batch_num = 0
    
    for raw_chunk in extract_parquet_chunks(str(sales_file), chunk_size=batch_size, max_records=limit):
        batch_num += 1
        b_start = time.time()
        
        # 1. Transform
        transformed_df = transform_sales(raw_chunk)
        
        # 2. Validate
        validated_df, metrics = validate_sales(transformed_df)
        total_rejected += metrics["rejected_records"]
        
        # 3. Load
        loaded_count = bulk_load_dataframe(
            df=validated_df,
            table_name="sale_events",
            conn=conn,
            primary_key="sale_id",
            use_staging_dedup=True
        )
        
        total_loaded += loaded_count
        b_elapsed = time.time() - b_start
        throughput = loaded_count / b_elapsed if b_elapsed > 0 else 0
        
        pct = (total_loaded / target_rows) * 100 if target_rows else 0
        logger.info(
            f"  [Batch {batch_num:03d}] Validated {len(validated_df):,} | Loaded {loaded_count:,} rows in {b_elapsed:.2f}s "
            f"({throughput:,.0f} rows/s) | Progress: {total_loaded:,}/{target_rows:,} ({pct:.1f}%)"
        )
              
    total_elapsed = time.time() - start_time
    avg_throughput = total_loaded / total_elapsed if total_elapsed > 0 else 0
    logger.info(
        f"[SALES COMPLETE] Loaded {total_loaded:,} sales (Rejected {total_rejected:,}) in {total_elapsed:.1f}s "
        f"(Avg: {avg_throughput:,.0f} rows/s)"
    )
    return total_loaded

def verify_database_counts(conn):
    """Queries and prints current row counts in PostgreSQL tables."""
    logger.info("=" * 60)
    logger.info("DATABASE VERIFICATION SUMMARY")
    logger.info("=" * 60)
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
        
    logger.info(f"  * Total Properties in DB : {prop_count:,}")
    logger.info(f"  * Total Sale Events in DB: {sale_count:,}")
    logger.info(f"  * Total Combined Records : {prop_count + sale_count:,}")
    logger.info(f"  * Linked Properties/Sales: {linked_parcels:,} distinct parcels")
    logger.info("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="NYC Real Estate Data Pipeline & ETL Orchestrator")
    parser.add_argument("--init-db", action="store_true", help="Initialize or reset database tables and indexes")
    parser.add_argument("--apply-views", action="store_true", default=True, help="Create analytical views")
    parser.add_argument("--sample", action="store_true", help="Use data/samples/ for fast demo/testing")
    parser.add_argument("--batch-size", type=int, default=int(os.getenv("BATCH_SIZE", 50000)), help="Rows per batch")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to process per dataset (optional)")
    parser.add_argument("--skip-properties", action="store_true", help="Skip loading properties table")
    parser.add_argument("--skip-sales", action="store_true", help="Skip loading sales table")
    
    args = parser.parse_args()
    
    env_limit = os.getenv("MAX_RECORDS")
    if args.limit is None and env_limit and env_limit.strip():
        args.limit = int(env_limit.strip())
        
    prop_file = find_data_file("properties-00000-of-00001.parquet", use_sample=args.sample)
    sales_file = find_data_file("sale_events-00000-of-00001.parquet", use_sample=args.sample)

    logger.info("=" * 60)
    logger.info("NYC REAL ESTATE ETL DATA PIPELINE")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mode: {'SAMPLE (FAST DEMO)' if args.sample else 'FULL / PRODUCTION'}")
    logger.info(f"Batch Size: {args.batch_size:,} | Limit: {f'{args.limit:,}' if args.limit else 'ALL'}")
    logger.info("=" * 60)
    
    # Start memory profiler
    tracemalloc.start()
    
    # 1. Test connection
    if not test_connection():
        logger.warning("Database is not reachable. Attempting to ensure database exists...")
        if not ensure_database_exists():
            logger.error("Please check your PostgreSQL service or edit your .env file.")
            sys.exit(1)
            
    conn = get_db_connection()
    
    try:
        # 2. Schema initialization
        if args.init_db:
            execute_sql_file(conn, SCHEMA_FILE, "Tables and Indexes Schema")
            
        # 3. Properties pipeline
        if not args.skip_properties:
            run_properties_pipeline(conn, prop_file=prop_file, batch_size=args.batch_size, limit=args.limit)
            
        # 4. Sales pipeline
        if not args.skip_sales:
            run_sales_pipeline(conn, sales_file=sales_file, batch_size=args.batch_size, limit=args.limit)
            
        # 5. Apply Analytical Views
        if args.apply_views:
            execute_sql_file(conn, VIEWS_FILE, "Analytical Business Intelligence Views")
            
        # 6. Verification
        verify_database_counts(conn)
        
        # Memory and Resource Profiling
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        logger.info(f"[PERFORMANCE AUDIT] Peak RAM Usage: {peak_mem / (1024 * 1024):.2f} MB")
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY!")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
