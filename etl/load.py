import io
import pandas as pd
import psycopg2
from typing import Optional

def bulk_load_dataframe(
    df: pd.DataFrame,
    table_name: str,
    conn: psycopg2.extensions.connection,
    primary_key: str = "record_id",
    use_staging_dedup: bool = True
) -> int:
    """
    High-performance bulk loader using PostgreSQL COPY FROM STDIN.
    
    Streams the Pandas DataFrame through an in-memory CSV buffer directly into
    PostgreSQL, offering 50-100x speedup over standard row-by-row inserts.
    
    When use_staging_dedup=True, loads into a temporary staging table and merges
    with 'ON CONFLICT (primary_key) DO NOTHING' to guarantee idempotent loading.
    
    Args:
        df: Pandas DataFrame containing cleaned records.
        table_name: Destination PostgreSQL table name.
        conn: Open psycopg2 database connection.
        primary_key: Primary key column name for conflict resolution.
        use_staging_dedup: If True, uses temp staging table for ON CONFLICT DO NOTHING.
        
    Returns:
        Number of rows successfully processed.
    """
    if df.empty:
        return 0
        
    cols = list(df.columns)
    col_str = ", ".join([f'"{c}"' for c in cols])
    
    # Format DataFrame to CSV in-memory buffer
    buffer = io.StringIO()
    df.to_csv(
        buffer,
        index=False,
        header=False,
        na_rep="",
        sep="\t",
        escapechar="\\"
    )
    buffer.seek(0)
    
    with conn.cursor() as cur:
        if use_staging_dedup:
            # Create a temporary staging table matching the destination table structure
            staging_table = f"temp_{table_name}_stage"
            cur.execute(f"CREATE TEMP TABLE {staging_table} (LIKE {table_name} INCLUDING DEFAULTS) ON COMMIT DROP;")
            
            # Fast COPY into staging table
            copy_sql = f"COPY {staging_table} ({col_str}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '', ESCAPE '\\')"
            cur.copy_expert(sql=copy_sql, file=buffer)
            
            # Merge into target table ignoring duplicate keys
            insert_sql = f"""
                INSERT INTO {table_name} ({col_str})
                SELECT {col_str} FROM {staging_table}
                ON CONFLICT ({primary_key}) DO NOTHING;
            """
            cur.execute(insert_sql)
        else:
            # Direct COPY
            copy_sql = f"COPY {table_name} ({col_str}) FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t', NULL '', ESCAPE '\\')"
            cur.copy_expert(sql=copy_sql, file=buffer)
            
    conn.commit()
    return len(df)

# Loading: COPY FROM STDIN protocol with in-memory buffer streaming
