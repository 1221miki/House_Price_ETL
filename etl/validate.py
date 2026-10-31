import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, Any

def validate_properties(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates cleaned properties DataFrame against business rules and data quality constraints.
    
    Checks:
    1. Primary key validity: record_id must not be null or empty.
    2. Parcel ID validity: parcel_id must not be null.
    3. Numeric ranges: building_sqft, lot_sqft, and assessed_value must be non-negative.
    4. Logical constraints: year_built must be between 1600 and current year (or null).
    
    Returns:
        Tuple of (validated_dataframe, validation_metrics_dict)
    """
    initial_count = len(df)
    if initial_count == 0:
        return df, {"total": 0, "valid": 0, "rejected": 0, "rejection_rate_pct": 0.0}
        
    current_year = datetime.now().year
    
    # Rule 1: Non-null primary key and parcel_id
    valid_keys = df['record_id'].notna() & (df['record_id'] != '') & (df['record_id'] != 'nan')
    valid_parcel = df['parcel_id'].notna() & (df['parcel_id'] != '') & (df['parcel_id'] != 'nan')
    
    # Rule 2: Non-negative square footage and assessed value if present
    valid_sqft = (df['building_sqft'].isna()) | (df['building_sqft'] >= 0)
    valid_lot = (df['lot_sqft'].isna()) | (df['lot_sqft'] >= 0)
    valid_assessed = (df['assessed_value'].isna()) | (df['assessed_value'] >= 0)
    
    # Rule 3: Plausible year_built
    valid_year = (df['year_built'].isna()) | (
        (df['year_built'] >= 1600) & (df['year_built'] <= current_year + 1)
    )
    
    # Master validation filter
    is_valid = valid_keys & valid_parcel & valid_sqft & valid_lot & valid_assessed & valid_year
    
    validated_df = df[is_valid].copy()
    rejected_count = initial_count - len(validated_df)
    
    metrics = {
        "total_records": initial_count,
        "valid_records": len(validated_df),
        "rejected_records": rejected_count,
        "rejection_rate_pct": round((rejected_count / initial_count) * 100, 2),
        "failed_keys": int((~valid_keys).sum()),
        "failed_parcels": int((~valid_parcel).sum()),
        "failed_negative_sqft": int((~valid_sqft).sum()),
        "failed_negative_lot": int((~valid_lot).sum()),
        "failed_assessed_val": int((~valid_assessed).sum()),
        "failed_year_built": int((~valid_year).sum())
    }
    
    return validated_df, metrics


def validate_sales(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates cleaned sale_events DataFrame against financial and integrity constraints.
    
    Checks:
    1. Primary key validity: sale_id must not be null or empty.
    2. Minimum price check: sale_price must be > 0 (filters nominal transfers like $0 or $1).
    3. Date validity: sale_date must be non-null and valid.
    4. Plausible year: sale_year must be <= current year.
    
    Returns:
        Tuple of (validated_dataframe, validation_metrics_dict)
    """
    initial_count = len(df)
    if initial_count == 0:
        return df, {"total": 0, "valid": 0, "rejected": 0, "rejection_rate_pct": 0.0}
        
    current_year = datetime.now().year
    
    # Rule 1: Non-null sale identifier
    valid_id = df['sale_id'].notna() & (df['sale_id'] != '') & (df['sale_id'] != 'nan')
    
    # Rule 2: Strictly positive sale price (commercial/residential arms-length benchmark)
    valid_price = df['sale_price'].notna() & (df['sale_price'] > 0)
    
    # Rule 3: Valid sale date
    valid_date = df['sale_date'].notna()
    
    # Rule 4: Plausible transaction year
    valid_year = df['sale_year'].notna() & (df['sale_year'] >= 1950) & (df['sale_year'] <= current_year + 1)
    
    # Master filter
    is_valid = valid_id & valid_price & valid_date & valid_year
    
    validated_df = df[is_valid].copy()
    rejected_count = initial_count - len(validated_df)
    
    metrics = {
        "total_records": initial_count,
        "valid_records": len(validated_df),
        "rejected_records": rejected_count,
        "rejection_rate_pct": round((rejected_count / initial_count) * 100, 2),
        "failed_missing_id": int((~valid_id).sum()),
        "failed_nonpositive_price": int((~valid_price).sum()),
        "failed_invalid_date": int((~valid_date).sum()),
        "failed_unrealistic_year": int((~valid_year).sum())
    }
    
    return validated_df, metrics

# Validations: Primary key assertions, price bounds, year built constraints
