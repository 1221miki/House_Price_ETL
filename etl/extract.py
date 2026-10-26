import os
import pyarrow.parquet as pq
import pandas as pd
from typing import Generator, List, Optional

def get_parquet_row_count(file_path: str) -> int:
    """Read parquet metadata to get total row count without loading data."""
    meta = pq.read_metadata(file_path)
    return meta.num_rows

def extract_parquet_chunks(
    file_path: str,
    columns: Optional[List[str]] = None,
    chunk_size: int = 50000,
    max_records: Optional[int] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Generator that extracts records from a Parquet file in memory-efficient chunks.
    Converts each batch directly to a Pandas DataFrame.
    
    Args:
        file_path: Absolute or relative path to the parquet file.
        columns: Optional list of columns to read.
        chunk_size: Number of records per chunk.
        max_records: Optional maximum total records to extract (useful for testing).
        
    Yields:
        pd.DataFrame containing at most chunk_size rows.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Parquet file not found at: {file_path}")
        
    parquet_file = pq.ParquetFile(file_path)
    total_yielded = 0
    
    for batch in parquet_file.iter_batches(batch_size=chunk_size, columns=columns):
        df_chunk = batch.to_pandas()
        
        if max_records is not None:
            remaining = max_records - total_yielded
            if remaining <= 0:
                break
            if len(df_chunk) > remaining:
                df_chunk = df_chunk.iloc[:remaining]
                
        total_yielded += len(df_chunk)
        yield df_chunk
        
        if max_records is not None and total_yielded >= max_records:
            break
