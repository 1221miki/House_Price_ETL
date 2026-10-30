
from pathlib import Path
import pyarrow.parquet as pq
import pandas as pd

data_dir = Path("Data")

files = [
    data_dir / "properties-00000-of-00001.parquet",
    data_dir / "sale_events-00000-of-00001.parquet",
]

for file in files:
    print("\n" + "=" * 60)

    if not file.exists():
        print(f"FILE NOT FOUND: {file}")
        continue

    parquet = pq.ParquetFile(file)

    print("File:", file.name)
    print("Total records:", parquet.metadata.num_rows)
    print("Total columns:", len(parquet.schema_arrow.names))
    print("Columns:", parquet.schema_arrow.names)

    df = pd.read_parquet(file).head(5)
    print("\nFirst 5 rows:")
    print(df.to_string(index=False))
