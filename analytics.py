import os
import pandas as pd
from config.database import get_db_connection

def run_query(conn, query: str, title: str):
    """Executes query and prints formatted summary."""
    print("\n" + "=" * 80)
    print(f"ANALYTICS REPORT: {title}")
    print("=" * 80)
    df = pd.read_sql_query(query, conn)
    if df.empty:
        print("No data available.")
    else:
        print(df.to_string(index=False))
    return df

def generate_business_reports():
    """Generates business intelligence reports from PostgreSQL analytical views."""
    conn = get_db_connection()
    try:
        # Report 1: Market Trends by Borough
        run_query(
            conn,
            """
            SELECT borough, sale_year, total_transactions, 
                   avg_sale_price, median_sale_price, avg_price_per_sqft, 
                   total_volume_millions
            FROM v_market_summary_by_borough_year
            WHERE sale_year >= 2020
            ORDER BY sale_year DESC, total_transactions DESC
            LIMIT 15;
            """,
            "1. RECENT NYC REAL ESTATE MARKET METRICS BY BOROUGH (2020-PRESENT)"
        )

        # Report 2: Property Type Performance
        run_query(
            conn,
            """
            SELECT property_type, total_sales, avg_sale_price, 
                   median_sale_price, avg_price_per_sqft, avg_property_age
            FROM v_property_type_performance
            ORDER BY total_sales DESC;
            """,
            "2. ASSET CLASS COMPARISON & METRICS BY PROPERTY TYPE"
        )

        # Report 3: Tax Assessment vs Market Valuation Equity
        run_query(
            conn,
            """
            SELECT borough, property_type,
                   COUNT(*) AS sample_size,
                   ROUND(AVG(sale_price), 2) AS avg_sale_price,
                   ROUND(AVG(assessed_value), 2) AS avg_assessed_value,
                   ROUND(AVG(sale_to_assessed_ratio), 2) AS avg_assessment_ratio
            FROM v_assessment_vs_market_price
            GROUP BY borough, property_type
            HAVING COUNT(*) >= 20
            ORDER BY sample_size DESC
            LIMIT 10;
            """,
            "3. TAX VALUATION EQUITY (SALES-TO-ASSESSMENT RATIO BY BOROUGH & TYPE)"
        )

        # Report 4: Top Appreciated Zip Codes
        run_query(
            conn,
            """
            SELECT zip_code, borough, total_sales, avg_sale_price, 
                   avg_price_per_sqft, median_sale_price
            FROM v_top_appreciated_zip_codes
            LIMIT 10;
            """,
            "4. TOP 10 HIGHEST VALUED ZIP CODES BY PRICE PER SQ FT"
        )

    finally:
        conn.close()

if __name__ == "__main__":
    generate_business_reports()
