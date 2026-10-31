import os
import sys
import argparse
from pathlib import Path
import pandas as pd

# Ensure project root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from config.database import get_db_engine

def render_ascii_bar_chart(df: pd.DataFrame, label_col: str, val_col: str, title: str, max_bars: int = 40):
    """Renders a simple ASCII bar chart in the console compatible with all encodings."""
    print("\n" + "-" * 70)
    print(f"VISUAL DISTRIBUTION: {title}")
    print("-" * 70)
    if df.empty or val_col not in df.columns:
        return
        
    valid_df = df.dropna(subset=[label_col, val_col])
    if valid_df.empty:
        return
        
    max_val = valid_df[val_col].max()
    if max_val <= 0:
        return
        
    for _, row in valid_df.iterrows():
        label = str(row[label_col])[:18].ljust(18)
        val = float(row[val_col])
        bar_len = int((val / max_val) * max_bars)
        bar = "#" * bar_len
        if "price" in val_col.lower():
            print(f"  {label} | {bar:<{max_bars}} | ${val:,.0f}")
        else:
            print(f"  {label} | {bar:<{max_bars}} | {val:,.2f}%" if "pct" in val_col.lower() else f"  {label} | {bar:<{max_bars}} | {val:,.0f}")
    print("-" * 70)

def run_query(engine, query: str, title: str, export_name: str = None, export_dir: Path = None):
    """Executes query, prints formatted summary, and optionally exports to CSV."""
    print("\n" + "=" * 80)
    print(f"ANALYTICS REPORT: {title}")
    print("=" * 80)
    df = pd.read_sql_query(query, engine)
    if df.empty:
        print("No data available.")
    else:
        print(df.to_string(index=False))
        
        # Optional CSV export
        if export_name and export_dir:
            export_dir.mkdir(parents=True, exist_ok=True)
            csv_path = export_dir / f"{export_name}.csv"
            df.to_csv(csv_path, index=False)
            print(f"  --> [Exported] {csv_path.name}")
            
    return df

def generate_business_reports(export_csv: bool = False):
    """Generates business intelligence reports from PostgreSQL analytical views."""
    engine = get_db_engine()
    export_dir = root_dir / "data" / "processed" if export_csv else None
    
    try:
        # Report 1: Market Trends by Borough
        df_borough = run_query(
            engine,
            """
            SELECT borough, sale_year, total_transactions, 
                   avg_sale_price, median_sale_price, avg_price_per_sqft, 
                   total_volume_millions
            FROM v_market_summary_by_borough_year
            WHERE sale_year >= 2020
            ORDER BY sale_year DESC, total_transactions DESC
            LIMIT 15;
            """,
            "1. RECENT NYC REAL ESTATE MARKET METRICS BY BOROUGH (2020-PRESENT)",
            export_name="borough_market_trends",
            export_dir=export_dir
        )
        if not df_borough.empty and "median_sale_price" in df_borough.columns:
            recent_boroughs = df_borough.drop_duplicates(subset=["borough"]).head(5)
            render_ascii_bar_chart(recent_boroughs, "borough", "median_sale_price", "Median Price by NYC Borough")

        # Report 2: Property Type Performance
        run_query(
            engine,
            """
            SELECT property_type, total_sales, avg_sale_price, 
                   median_sale_price, avg_price_per_sqft, avg_property_age
            FROM v_property_type_performance
            ORDER BY total_sales DESC;
            """,
            "2. ASSET CLASS COMPARISON & METRICS BY PROPERTY TYPE",
            export_name="property_type_metrics",
            export_dir=export_dir
        )

        # Report 3: Tax Assessment vs Market Valuation Equity
        run_query(
            engine,
            """
            SELECT borough, property_type,
                   COUNT(*) AS sample_size,
                   ROUND(AVG(sale_price), 2) AS avg_sale_price,
                   ROUND(AVG(assessed_value), 2) AS avg_assessed_value,
                   ROUND(AVG(sale_to_assessed_ratio), 2) AS avg_assessment_ratio
            FROM v_assessment_vs_market_price
            GROUP BY borough, property_type
            HAVING COUNT(*) >= 10
            ORDER BY sample_size DESC
            LIMIT 15;
            """,
            "3. ASSESSMENT-TO-SALE RATIO EQUITY AUDIT BY BOROUGH & ASSET TYPE",
            export_name="tax_equity_audit",
            export_dir=export_dir
        )

        # Report 4: Top Appreciated Zip Codes
        df_zip = run_query(
            engine,
            """
            SELECT zip_code, borough, total_sales, 
                   avg_sale_price, avg_price_per_sqft, median_sale_price
            FROM v_top_appreciated_zip_codes
            LIMIT 15;
            """,
            "4. TOP VALUED NEIGHBORHOOD ZIP CODES BY PRICE/SQFT (NYC)",
            export_name="top_appreciated_zip_codes",
            export_dir=export_dir
        )
        if not df_zip.empty and "avg_price_per_sqft" in df_zip.columns:
            render_ascii_bar_chart(df_zip.head(8), "zip_code", "avg_price_per_sqft", "Top Zip Codes by Price/Sqft ($)")

        if export_csv:
            print("\n" + "=" * 80)
            print(f"[SUCCESS] All BI CSV reports exported to {export_dir.resolve()}")
            print("Ready to open in Excel, Tableau, or PowerBI for presentation slides!")
            print("=" * 80)

    finally:
        engine.dispose()

def main():
    parser = argparse.ArgumentParser(description="Automated Real Estate Analytics & BI Reporting")
    parser.add_argument("--export-csv", action="store_true", help="Export analytical tables to data/processed/ CSV files")
    args = parser.parse_args()
    
    generate_business_reports(export_csv=args.export_csv)

if __name__ == "__main__":
    main()

# Analytics engine: Generates terminal ASCII bar charts and exports CSVs
