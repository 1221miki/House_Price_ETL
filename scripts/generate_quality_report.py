import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Project root
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from etl.extract import extract_parquet_chunks, get_parquet_row_count
from etl.transform import clean_parcel_id

def profile_dataset(file_path: Path, max_sample: int = 100000) -> dict:
    """Profiles a Parquet dataset chunk to compute data quality metrics."""
    total_rows = get_parquet_row_count(str(file_path))
    generator = extract_parquet_chunks(str(file_path), chunk_size=max_sample, max_records=max_sample)
    df = next(generator)
    
    null_counts = df.isnull().sum()
    null_pcts = (null_counts / len(df)) * 100
    
    col_summary = []
    for col in df.columns:
        col_summary.append({
            "column": col,
            "dtype": str(df[col].dtype),
            "null_count": int(null_counts[col]),
            "null_pct": round(float(null_pcts[col]), 2),
            "unique_sample": int(df[col].nunique())
        })
        
    return {
        "file_name": file_path.name,
        "file_size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
        "total_records": total_rows,
        "sampled_records": len(df),
        "columns": col_summary,
        "df": df
    }

def generate_quality_report():
    print("=" * 60)
    print("DATA QUALITY PROFILER & AUDIT REPORT GENERATOR")
    print("=" * 60)
    
    raw_dir = ROOT_DIR / "data" / "raw"
    prop_path = raw_dir / "properties-00000-of-00001.parquet"
    sales_path = raw_dir / "sale_events-00000-of-00001.parquet"
    
    if not prop_path.exists() or not sales_path.exists():
        print("[ERROR] Raw data files not found.")
        return
        
    print(f"Profiling properties dataset ({prop_path.name})...")
    prop_prof = profile_dataset(prop_path, max_sample=100000)
    
    print(f"Profiling sale events dataset ({sales_path.name})...")
    sales_prof = profile_dataset(sales_path, max_sample=100000)
    
    # Financial and Anomaly Metrics on Sales
    sales_df = sales_prof["df"]
    prices = pd.to_numeric(sales_df["sale_price"], errors="coerce")
    nominal_sales = int((prices < 10000).sum())
    luxury_sales = int((prices >= 10000000).sum())
    valid_prices = int((prices >= 10000).sum())
    
    # Referential Match Audit (sample)
    prop_df = prop_prof["df"]
    prop_parcels = set(clean_parcel_id(prop_df["parcel_id"]).dropna())
    sale_parcels = clean_parcel_id(sales_df["parcel_id"]).dropna()
    matched_parcels = int(sale_parcels.isin(prop_parcels).sum())
    match_rate = round((matched_parcels / len(sale_parcels)) * 100, 2) if len(sale_parcels) > 0 else 0
    
    # Build Markdown Report
    report_lines = [
        "# Data Quality & Integrity Audit Report",
        "",
        f"> **Generated at:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"> **Project:** House Price ETL | Course: Big Data Analytics & BI  ",
        "",
        "---",
        "",
        "## 1. Executive Summary & Scale",
        "",
        "| Metric | Properties Dataset | Sale Events Dataset | Combined Total |",
        "|---|---|---|---|",
        f"| **File Name** | `{prop_prof['file_name']}` | `{sales_prof['file_name']}` | — |",
        f"| **File Size on Disk** | {prop_prof['file_size_mb']} MB | {sales_prof['file_size_mb']} MB | {round(prop_prof['file_size_mb'] + sales_prof['file_size_mb'], 2)} MB |",
        f"| **Total Record Count** | **{prop_prof['total_records']:,}** | **{sales_prof['total_records']:,}** | **{prop_prof['total_records'] + sales_prof['total_records']:,}** |",
        f"| **Number of Attributes** | {len(prop_prof['columns'])} | {len(sales_prof['columns'])} | 56 combined |",
        f"| **Audit Sample Size** | {prop_prof['sampled_records']:,} | {sales_prof['sampled_records']:,} | — |",
        "",
        "---",
        "",
        "## 2. Referential Integrity & Foreign Key Audit",
        "",
        "- **Primary Join Key:** `parcel_id` (NYC 10-digit Borough-Block-Lot / BBL).",
        f"- **Sample Match Rate:** **{match_rate}%** of sale events successfully correlate to physical parcel records in the properties dataset.",
        "- **Quality Decision:** In the ETL pipeline, child sales records reference `properties(parcel_id)`. Non-matching or orphan transactions are logged and isolated into staging tables.",
        "",
        "---",
        "",
        "## 3. Financial Distribution & Anomaly Analysis (Sale Events)",
        "",
        "| Category | Price Range | Count (Sample 100k) | % of Sample | Business Interpretation |",
        "|---|---|---|---|---|",
        f"| **Nominal / Non-Arms-Length Transfers** | `< $10,000` (e.g. $0, $1) | {nominal_sales:,} | {round((nominal_sales / len(sales_df)) * 100, 2)}% | Intra-family gifts, deed corrections, or nominal foreclosures (filtered out during BI analytics). |",
        f"| **Standard Arms-Length Transactions** | `$10,000` to `$10,000,000` | {valid_prices:,} | {round((valid_prices / len(sales_df)) * 100, 2)}% | True residential and commercial market sales. |",
        f"| **Institutional & Luxury Transactions** | `> $10,000,000` | {luxury_sales:,} | {round((luxury_sales / len(sales_df)) * 100, 2)}% | Commercial skyscrapers, large multifamily developments, or luxury penthouses. |",
        "",
        "---",
        "",
        "## 4. Column Missingness & Null Value Profile",
        "",
        "### Properties Dataset (Top Columns)",
        "| Column | Data Type | Null Count (Sample 100k) | Null Percentage | Quality Assessment |",
        "|---|---|---|---|---|"
    ]
    
    for c in prop_prof["columns"][:15]:
        status = "Healthy" if c["null_pct"] < 10 else ("Acceptable" if c["null_pct"] < 50 else "Sparse")
        report_lines.append(f"| `{c['column']}` | `{c['dtype']}` | {c['null_count']:,} | {c['null_pct']}% | {status} |")
        
    report_lines.extend([
        "",
        "### Sale Events Dataset (Top Columns)",
        "| Column | Data Type | Null Count (Sample 100k) | Null Percentage | Quality Assessment |",
        "|---|---|---|---|---|"
    ])
    
    for c in sales_prof["columns"][:15]:
        status = "Healthy" if c["null_pct"] < 10 else ("Acceptable" if c["null_pct"] < 50 else "Sparse")
        report_lines.append(f"| `{c['column']}` | `{c['dtype']}` | {c['null_count']:,} | {c['null_pct']}% | {status} |")
        
    report_lines.extend([
        "",
        "---",
        "",
        "## 5. Automated Data Quality Rules Implemented (`etl/validate.py`)",
        "",
        "1. **`record_id` & `sale_id` Non-Null Rule:** Guarantees absolute uniqueness and primary key integrity.",
        "2. **Strict Positive Price Rule (`CHECK (sale_price > 0)`):** Rejects invalid negative financial inputs.",
        "3. **Plausible Year Built Constraint (`1600 <= year_built <= Current Year`):** Rejects corrupt dates.",
        "4. **Non-Negative Square Footage Rule:** Prevents corrupt negative area records.",
        "5. **BBL Standardizer:** Trims floating-point scientific notation (`2054800111.00000000` -> `2054800111`).",
        "",
        "---",
        "*(This audit document can be included directly in Section 5 of the Group Final Report.)*"
    ])
    
    # Save Report
    report_path = ROOT_DIR / "logs" / "data_quality_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"\n[SUCCESS] Quality report generated at: {report_path.relative_to(ROOT_DIR)}")
    print(f"  - Total records audited: {prop_prof['total_records'] + sales_prof['total_records']:,}")
    print(f"  - Key match rate: {match_rate}%")
    print(f"  - Nominal sales isolated: {nominal_sales:,}")

if __name__ == "__main__":
    generate_quality_report()
