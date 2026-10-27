from pathlib import Path
import pyarrow.parquet as pq

def main():
    total = 0
    # Determine base directory (project root)
    script_dir = Path(__file__).resolve().parent
    base_dir = script_dir.parent if script_dir.name == "scripts" else script_dir
    
    # Search data directory recursively for parquet files
    data_dir = base_dir / "data"
    if not data_dir.exists():
        data_dir = base_dir / "Data"
        
    parquet_files = sorted(list(data_dir.rglob("*.parquet")))
    if not parquet_files:
        print(f"No parquet files found in {data_dir.resolve()}")
        return

    for file in parquet_files:
        pf = pq.ParquetFile(file)
        rows = pf.metadata.num_rows
        total += rows
        print("\n" + "=" * 60)
        print("FILE:", file.relative_to(base_dir))
        print("Records:", f"{rows:,}")
        print("Columns:", len(pf.schema.names))
        for name, typ in zip(pf.schema_arrow.names, pf.schema_arrow.types):
            print(f"  - {name:<22} | {typ}")
        print("Row groups:", pf.num_row_groups)
        
    print("\n" + "=" * 60)
    print("TOTAL records across all inspected files:", f"{total:,}")
    print("=" * 60)

if __name__ == "__main__":
    main()
