"""
etl_pipeline.py - Extract (PyArrow) -> Transform (Pandas) -> Load (PostgreSQL)
Group Assignment: Designing a Simple Data Pipeline and ETL Process
Project: House Price ETL
"""

import os
import sys
import time
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load .env configuration
load_dotenv()

# ===================== CONFIG: REAL COLUMNS =====================
DB_URL = os.getenv("DB_URL") or (
    f"postgresql+psycopg2://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'house_price_db')}"
)

data_dir = Path("Data") if Path("Data").exists() else Path("data")
PROP_FILE = data_dir / "properties-00000-of-00001.parquet"
SALE_FILE = data_dir / "sale_events-00000-of-00001.parquet"
BATCH = 100_000

# Mapping real columns from Hugging Face Parquet dataset
PROP_RAW_KEY = "parcel_id"
PROP_KEY = "property_id"
PROP_KEEP = ["property_id", "property_type", "city", "state", "zip_code", "building_sqft", "lot_sqft", "year_built", "bedrooms", "assessed_value"]
PROP_NUM = ["building_sqft", "lot_sqft", "year_built", "bedrooms", "assessed_value"]

SALE_RAW_KEY = "parcel_id"
SALE_KEY = "property_id"
SALE_KEEP = ["property_id", "sale_date", "sale_price", "building_sqft", "year_built"]
SALE_NUM = ["sale_price", "building_sqft", "year_built"]
SALE_DATE = ["sale_date"]
PRICE_COL = "sale_price"
# =========================================================================

stats = {
    "props_read": 0,
    "props_loaded": 0,
    "props_dupes": 0,
    "sales_read": 0,
    "sales_loaded": 0,
    "sales_bad_price": 0,
    "sales_orphans": 0,
    "sales_dupes": 0
}

def clean_props(df, seen):
    """
    Transform and clean properties data:
    - Normalizes parcel_id into standardized property_id
    - Converts numerical columns
    - Drops duplicates within batch and against previously seen IDs
    """
    df = df.copy()
    # Normalize BBL parcel_id (e.g. '2054800111.00000000' -> '2054800111')
    if PROP_RAW_KEY in df.columns:
        df[PROP_KEY] = (
            df[PROP_RAW_KEY].astype(str)
            .str.split('.').str[0]
            .str.strip()
            .replace(['nan', 'None', '', '<NA>'], None)
        )
        
    df = df[[c for c in PROP_KEEP if c in df.columns]].copy()
    for c in PROP_NUM:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    df = df.dropna(subset=[PROP_KEY]).drop_duplicates()
    before = len(df)
    df = df[~df[PROP_KEY].isin(seen)].drop_duplicates(subset=[PROP_KEY])
    stats["props_dupes"] += before - len(df)
    seen.update(df[PROP_KEY].tolist())
    return df

def clean_sales(df, valid_ids):
    """
    Transform and clean sales event data:
    - Normalizes parcel_id into standardized property_id
    - Converts numbers and dates
    - Removes duplicate rows
    - Removes zero or negative prices
    - Rejects orphan sales whose property_id does not exist in properties
    """
    df = df.copy()
    if SALE_RAW_KEY in df.columns:
        df[SALE_KEY] = (
            df[SALE_RAW_KEY].astype(str)
            .str.split('.').str[0]
            .str.strip()
            .replace(['nan', 'None', '', '<NA>'], None)
        )
        
    df = df[[c for c in SALE_KEEP if c in df.columns]].copy()
    for c in SALE_NUM:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    for c in SALE_DATE:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
            
    n0 = len(df)
    df = df.drop_duplicates()
    stats["sales_dupes"] += n0 - len(df)
    
    n1 = len(df)
    df = df[df[PRICE_COL] > 0]
    stats["sales_bad_price"] += n1 - len(df)
    
    n2 = len(df)
    df = df[df[SALE_KEY].isin(valid_ids)]
    stats["sales_orphans"] += n2 - len(df)
    
    return df

def load_file(path, table, engine, cleaner, arg, read_key, load_key, max_rows=None):
    """Reads Parquet file in batches, cleans, and loads into PostgreSQL."""
    pf = pq.ParquetFile(path)
    total_source = pf.metadata.num_rows
    print(f"\n{table}: {total_source:,} source rows in Parquet")
    
    batch_count = 0
    total_processed = 0
    
    for batch in pf.iter_batches(batch_size=BATCH):
        batch_count += 1
        df = batch.to_pandas()
        
        if max_rows and total_processed >= max_rows:
            break
        if max_rows and (total_processed + len(df)) > max_rows:
            df = df.iloc[:(max_rows - total_processed)]
            
        stats[read_key] += len(df)
        total_processed += len(df)
        
        df = cleaner(df, arg)
        if len(df):
            df.to_sql(
                table,
                engine,
                if_exists="append",
                index=False,
                chunksize=10_000,
                method="multi"
            )
            stats[load_key] += len(df)
            
        print(f"  Batch {batch_count:02d}: read {stats[read_key]:,} | loaded {stats[load_key]:,}")
        
        if max_rows and total_processed >= max_rows:
            break

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run ETL Pipeline for House Price Data")
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit for test runs (e.g. 50000)")
    parser.add_argument("--skip-schema", action="store_true", help="Skip schema execution")
    args = parser.parse_args()

    t0 = time.time()
    print("=" * 60)
    print("STARTING HOUSE PRICE ETL PIPELINE")
    print(f"Connecting to: {DB_URL.split('@')[-1] if '@' in DB_URL else DB_URL}")
    print("=" * 60)

    try:
        engine = create_engine(DB_URL)
        with engine.connect() as con:
            print("Successfully connected to PostgreSQL.")
    except Exception as e:
        print(f"\n[ERROR] Database connection failed:\n{e}")
        print("\nPlease ensure PostgreSQL is running and your DB_URL / .env credentials are correct.")
        sys.exit(1)

    if not args.skip_schema:
        schema_path = Path("schema.sql")
        if schema_path.exists():
            print("\nExecuting schema.sql to create tables and indexes...")
            with engine.begin() as con:
                con.execute(text(schema_path.read_text(encoding="utf-8")))
            print("schema.sql executed successfully.")

    seen_ids = set()
    load_file(PROP_FILE, "properties", engine, clean_props, seen_ids, "props_read", "props_loaded", max_rows=args.limit)
    load_file(SALE_FILE, "sale_events", engine, clean_sales, seen_ids, "sales_read", "sales_loaded", max_rows=args.limit)

    print("\n" + "=" * 60)
    print("=== DATA QUALITY SUMMARY ===")
    print("=" * 60)
    for k, v in stats.items():
        print(f"{k:18}: {v:,}")

    print("\n" + "=" * 60)
    print("=== POSTGRESQL ROW COUNTS ===")
    print("=" * 60)
    with engine.connect() as con:
        for t in ("properties", "sale_events"):
            count = con.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"{t:18}: {count:,} rows")

    print(f"\nDone in {round(time.time() - t0, 1)} seconds.")
