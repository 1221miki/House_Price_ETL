from pathlib import Path
import pyarrow.parquet as pq

def main():
    total = 0
    # Search in both 'Data' and 'data' directories
    data_dir = Path("Data") if Path("Data").exists() else Path("data")
    
    parquet_files = list(data_dir.glob("*.parquet"))
    if not parquet_files:
        print(f"No parquet files found in {data_dir.resolve()}")
        return

    for file in sorted(parquet_files):
        pf = pq.ParquetFile(file)
        rows = pf.metadata.num_rows
        total += rows
        print("\n" + "=" * 50)
        print("FILE:", file.name)
        print("Records:", f"{rows:,}")
        print("Columns:", len(pf.schema.names))
        for name, typ in zip(pf.schema_arrow.names, pf.schema_arrow.types):
            print("  -", name, "|", typ)
        print("Row groups:", pf.num_row_groups)
        
    print("\n" + "=" * 50)
    print("TOTAL records in all files:", f"{total:,}")
    print("=" * 50)

if __name__ == "__main__":
    main()
