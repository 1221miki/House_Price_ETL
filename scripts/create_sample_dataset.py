import os
import sys
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

# Project root
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from etl.extract import extract_parquet_chunks

def create_sample_datasets(sample_size: int = 25000):
    """
    Creates referentially consistent sample Parquet datasets in data/samples/
    by extracting N properties and their corresponding sale events.
    """
    raw_dir = ROOT_DIR / "data" / "raw"
    sample_dir = ROOT_DIR / "data" / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    prop_raw = raw_dir / "properties-00000-of-00001.parquet"
    sales_raw = raw_dir / "sale_events-00000-of-00001.parquet"
    
    if not prop_raw.exists() or not sales_raw.exists():
        print(f"[ERROR] Source parquet files not found in {raw_dir}")
        return False
        
    print(f"Generating representative sample datasets ({sample_size:,} records)...")
    
    # 1. Sample properties
    print(f"  1. Extracting {sample_size:,} properties...")
    prop_gen = extract_parquet_chunks(str(prop_raw), chunk_size=sample_size, max_records=sample_size)
    prop_sample_df = next(prop_gen)
    
    prop_sample_file = sample_dir / "properties_sample.parquet"
    prop_sample_df.to_parquet(prop_sample_file, index=False)
    print(f"     [Saved] {prop_sample_file.name} ({len(prop_sample_df):,} rows)")
    
    # 2. Extract matching sales events (to ensure foreign key integrity)
    sampled_parcels = set(prop_sample_df["parcel_id"].dropna().astype(str).str.split('.').str[0].str.strip())
    print(f"  2. Extracting matching sale events for {len(sampled_parcels):,} sampled parcels...")
    
    matched_sales = []
    total_sales_checked = 0
    
    for sales_chunk in extract_parquet_chunks(str(sales_raw), chunk_size=50000, max_records=250000):
        total_sales_checked += len(sales_chunk)
        clean_parcels = sales_chunk["parcel_id"].astype(str).str.split('.').str[0].str.strip()
        matching_mask = clean_parcels.isin(sampled_parcels)
        matched_chunk = sales_chunk[matching_mask]
        
        if not matched_chunk.empty:
            matched_sales.append(matched_chunk)
            
        if sum(len(m) for m in matched_sales) >= sample_size:
            break
            
    if matched_sales:
        sales_sample_df = pd.concat(matched_sales, ignore_index=True).iloc[:sample_size]
    else:
        # Fallback to direct chunk
        sales_gen = extract_parquet_chunks(str(sales_raw), chunk_size=sample_size, max_records=sample_size)
        sales_sample_df = next(sales_gen)
        
    sales_sample_file = sample_dir / "sale_events_sample.parquet"
    sales_sample_df.to_parquet(sales_sample_file, index=False)
    print(f"     [Saved] {sales_sample_file.name} ({len(sales_sample_df):,} rows)")
    
    print("\n[SUCCESS] Sample datasets created in data/samples/ for instant demos and testing!")
    return True

if __name__ == "__main__":
    create_sample_datasets()
