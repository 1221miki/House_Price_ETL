from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

base_dir = Path(__file__).resolve().parent
candidates = [
    base_dir / "Data" / "raw",
    base_dir / "data" / "raw",
    base_dir / "Data",
    base_dir / "data",
]

data_dir = next((d for d in candidates if (d / "properties-00000-of-00001.parquet").exists()), base_dir / "Data" / "raw")

files = [
    data_dir / "properties-00000-of-00001.parquet",
    data_dir / "sale_events-00000-of-00001.parquet",
]

total_rows = 0
for file in files:
    print("\n" + "=" * 60)

    if not file.exists():
        print(f"FILE NOT FOUND: {file}")
        continue

    parquet = pq.ParquetFile(file)
    rows = parquet.metadata.num_rows
    total_rows += rows

    print("File:", file.name)
    print("Total records:", f"{rows:,}")
    print("Total columns:", len(parquet.schema_arrow.names))
    print("Columns sample:", parquet.schema_arrow.names[:8], "...")

    df = pd.read_parquet(file).head(3)
    print("\nFirst 3 rows preview:")
    print(df.iloc[:, :6].to_string(index=False))

print("\n" + "=" * 60)
print(f"TOTAL SOURCE RECORDS: {total_rows:,}")
print("=" * 60)
