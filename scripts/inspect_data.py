import sys
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

# Setup base directory
BASE_DIR = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "scripts" else Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def find_parquet():
    candidates = [
        BASE_DIR / "Data" / "raw" / "sale_events-00000-of-00001.parquet",
        BASE_DIR / "data" / "raw" / "sale_events-00000-of-00001.parquet",
        BASE_DIR / "Data" / "samples" / "sale_events_sample.parquet",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def main():
    file_path = find_parquet()
    if not file_path:
        print("[ERROR] Parquet dataset not found.")
        return

    # Read Parquet File
    pf = pq.ParquetFile(file_path)
    total_records = pf.metadata.num_rows

    # Read first 50,000 chunk for deep audit & instant speed
    batch = next(pf.iter_batches(batch_size=50000))
    df = batch.to_pandas()

    # Select key business columns for clean terminal display
    display_cols = [c for c in ['record_id', 'parcel_id', 'borough', 'sale_price', 'sale_date', 'building_sqft', 'year_built'] if c in df.columns]
    if len(display_cols) < 5:
        display_cols = df.columns[:6].tolist()

    df_first10 = df.head(10)[display_cols]

    print("--- First 10 Records ---")
    print(df_first10.to_string(index=True))

    print("\n--- Column Names ---")
    print(df.columns.tolist())

    print("\n--- Data Types ---")
    print(df.dtypes.to_string())

    print("\n--- Missing Values in First 10 Records ---")
    print(df.head(10).isnull().sum().to_string())

    print("\n--- Entire Dataset Results ---")
    print(f"Total records: {total_records:,}")

    print("\n--- Missing Values in Entire Dataset (Audited Sample) ---")
    print(df.isnull().sum().to_string())

    print("\n--- Duplicate Records ---")
    dup_count = df.duplicated(subset=['record_id' if 'record_id' in df.columns else df.columns[0]]).sum()
    print(f"Duplicate records within chunks: {dup_count}")

if __name__ == "__main__":
    main()

