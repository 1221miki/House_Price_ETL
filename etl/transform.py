import pandas as pd
import numpy as np

BOROUGH_MAP = {
    '1': 'Manhattan',
    '2': 'Bronx',
    '3': 'Brooklyn',
    '4': 'Queens',
    '5': 'Staten Island'
}

def clean_parcel_id(series: pd.Series) -> pd.Series:
    """
    Standardize NYC Parcel IDs (Borough-Block-Lot / BBL).
    Removes trailing decimals (e.g. '2054800111.00000000' -> '2054800111').
    """
    return (
        series.fillna('')
        .astype(str)
        .str.replace(r'\..*$', '', regex=True)
        .str.strip()
        .replace(['nan', 'None', '', '<NA>', 'null', 'NULL'], np.nan)
    )

def derive_borough(df: pd.DataFrame) -> pd.Series:
    """
    Derives borough name using the first character of the standardized parcel_id,
    falling back to existing 'city' column.
    """
    bbl_prefix = df['parcel_id'].fillna('').astype(str).str[0]
    mapped = bbl_prefix.map(BOROUGH_MAP)
    
    if 'city' in df.columns:
        return mapped.fillna(df['city'])
    return mapped.fillna('Unknown')

def clean_zip_code(series: pd.Series) -> pd.Series:
    """Standardize zip code format to 5 digits."""
    cleaned = (
        series.fillna('')
        .astype(str)
        .str.replace(r'\..*$', '', regex=True)
        .str.strip()
        
    )
    return cleaned.apply(lambda z: z.zfill(5) if z and z.isdigit() and z != '00000' and int(z) > 0 else np.nan)

def transform_properties(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform and clean raw NYC PLUTO properties chunk.
    """
    df = df.copy()
    
    # 1. Clean IDs
    df['record_id'] = df['record_id'].astype(str).str.strip()
    df['parcel_id'] = clean_parcel_id(df['parcel_id'])
    
    # Filter out records without primary keys
    df = df.dropna(subset=['record_id', 'parcel_id'])
    df = df[df['parcel_id'] != '']
    
    # Deduplicate within batch
    df = df.drop_duplicates(subset=['record_id'])
    
    # 2. Ensure optional columns exist
    for col in [
        'city', 'state', 'zip_code', 'country', 'address_line', 'unit',
        'property_type', 'property_class_raw', 'zoning', 'school_district',
        'latitude', 'longitude', 'building_sqft', 'lot_sqft', 'year_built',
        'stories', 'units_total', 'assessed_value', 'assessed_land_value',
        'market_value', 'assessment_year'
    ]:
        if col not in df.columns:
            df[col] = np.nan

    # 3. Derive geographic fields
    df['borough'] = derive_borough(df)
    df['city'] = df['city'].fillna(df['borough']).astype(str).str.strip().str.title()
    df['state'] = df['state'].fillna('NY').astype(str).str.strip().str.upper()
    df['zip_code'] = clean_zip_code(df['zip_code'])
    df['country'] = df['country'].fillna('US').astype(str).str.strip().str.upper()
    
    # 4. Clean textual fields
    df['address_line'] = df['address_line'].astype(str).replace(['nan', 'None', '<NA>'], '').str.strip().str.upper()
    df['unit'] = df['unit'].astype(str).replace(['nan', 'None', '<NA>'], '').str.strip().str.upper()
    df['unit'] = df['unit'].replace(['NAN', 'NONE', ''], None)
    df['property_type'] = df['property_type'].fillna('unknown').astype(str).str.strip().str.lower()
    df['property_class_raw'] = df['property_class_raw'].fillna('').astype(str).str.strip().str.slice(0, 100)
    df['zoning'] = df['zoning'].fillna('').astype(str).str.strip()
    df['school_district'] = df['school_district'].astype(str).str.split('.').str[0].str.strip()
    df['school_district'] = df['school_district'].replace(['nan', 'None', ''], None)
    
    # 5. Numeric and type validation
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    df['building_sqft'] = pd.to_numeric(df['building_sqft'], errors='coerce').clip(lower=0)
    df['lot_sqft'] = pd.to_numeric(df['lot_sqft'], errors='coerce').clip(lower=0)
    
    # Year built: allow valid historic and modern years (1600 - 2026) as nullable Int64
    year_built = pd.to_numeric(df['year_built'], errors='coerce')
    clean_year = np.where((year_built >= 1600) & (year_built <= 2026), year_built, np.nan)
    df['year_built'] = pd.Series(clean_year, dtype='Int64')
    
    df['stories'] = pd.to_numeric(df['stories'], errors='coerce').clip(lower=0, upper=150)
    df['units_total'] = pd.Series(pd.to_numeric(df['units_total'], errors='coerce').clip(lower=0), dtype='Int64')
    
    df['assessed_value'] = pd.to_numeric(df['assessed_value'], errors='coerce').clip(lower=0)
    df['assessed_land_value'] = pd.to_numeric(df['assessed_land_value'], errors='coerce').clip(lower=0)
    df['market_value'] = pd.to_numeric(df['market_value'], errors='coerce').clip(lower=0)
    
    df['assessment_year'] = pd.Series(pd.to_numeric(df['assessment_year'], errors='coerce'), dtype='Int64')
    
    target_columns = [
        'record_id', 'parcel_id', 'borough', 'address_line', 'unit', 'city', 'state',
        'zip_code', 'country', 'latitude', 'longitude', 'property_type',
        'property_class_raw', 'building_sqft', 'lot_sqft', 'year_built', 'stories',
        'units_total', 'zoning', 'school_district', 'assessed_value',
        'assessed_land_value', 'market_value', 'assessment_year'
    ]
    
    return df[target_columns]

def transform_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform and clean raw NYC sale events chunk.
    """
    df = df.copy()
    
    # 1. Clean primary keys
    if 'record_id' in df.columns and 'sale_id' not in df.columns:
        df['sale_id'] = df['record_id'].astype(str).str.strip()
    elif 'sale_id' in df.columns:
        df['sale_id'] = df['sale_id'].astype(str).str.strip()
        
    df['parcel_id'] = clean_parcel_id(df['parcel_id'])
    
    # Drop rows without sale_id
    df = df.dropna(subset=['sale_id'])
    df = df.drop_duplicates(subset=['sale_id'])
    
    # 2. Date parsing and temporal features
    df['sale_date_dt'] = pd.to_datetime(df['sale_date'], errors='coerce')
    df = df.dropna(subset=['sale_date_dt'])
    
    df['sale_date'] = df['sale_date_dt'].dt.date
    df['sale_year'] = pd.Series(df['sale_date_dt'].dt.year, dtype='Int64')
    df['sale_quarter'] = pd.Series(df['sale_date_dt'].dt.quarter, dtype='Int64')
    df['sale_month'] = pd.Series(df['sale_date_dt'].dt.month, dtype='Int64')
    
    # 3. Numeric conversions & cleaning
    df['sale_price'] = pd.to_numeric(df['sale_price'], errors='coerce')
    df = df[df['sale_price'] > 0]
    
    df['building_sqft'] = pd.to_numeric(df['building_sqft'], errors='coerce')
    
    year_num = pd.to_numeric(df['year_built'], errors='coerce')
    clean_year = np.where((year_num >= 1600) & (year_num <= 2026), year_num, np.nan)
    df['year_built'] = pd.Series(clean_year, dtype='Int64')
    
    # 4. Feature Engineering
    valid_sqft = (df['building_sqft'] > 50) & (df['building_sqft'] < 2000000)
    df['price_per_sqft'] = np.where(valid_sqft, (df['sale_price'] / df['building_sqft']).round(2), np.nan)
    
    age = np.where(
        df['year_built'].notnull(),
        (df['sale_year'] - df['year_built']).clip(lower=0, upper=300),
        np.nan
    )
    df['property_age_at_sale'] = pd.Series(age, dtype='Int64')
    
    # 5. Geographic & Address cleaning
    for col in ['address_line', 'unit', 'city', 'state', 'zip_code', 'country', 'latitude', 'longitude', 'property_class_raw']:
        if col not in df.columns:
            df[col] = np.nan
    if 'is_multi_parcel' not in df.columns:
        df['is_multi_parcel'] = False

    df['borough'] = derive_borough(df)
    df['city'] = df['city'].fillna(df['borough']).astype(str).str.strip().str.title()
    df['state'] = df['state'].fillna('NY').astype(str).str.strip().str.upper()
    df['zip_code'] = clean_zip_code(df['zip_code'])
    df['country'] = df['country'].fillna('US').astype(str).str.strip().str.upper()
    df['address_line'] = df['address_line'].astype(str).replace(['nan', 'None', '<NA>'], '').str.strip().str.upper()
    df['unit'] = df['unit'].astype(str).replace(['nan', 'None', '<NA>'], '').str.strip().str.upper()
    df['unit'] = df['unit'].replace(['NAN', 'NONE', ''], None)
    
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['property_class_raw'] = df['property_class_raw'].fillna('').astype(str).str.strip().str.slice(0, 100)
    df['is_multi_parcel'] = df['is_multi_parcel'].fillna(False).astype(bool)
    
    target_columns = [
        'sale_id', 'parcel_id', 'borough', 'address_line', 'unit', 'city', 'state',
        'zip_code', 'country', 'latitude', 'longitude', 'property_class_raw',
        'sale_price', 'sale_date', 'sale_year', 'sale_quarter', 'sale_month',
        'building_sqft', 'price_per_sqft', 'year_built', 'property_age_at_sale',
        'is_multi_parcel'
    ]
    
    return df[target_columns]

# Transformations: BBL regex cleaning, arms-length filtering, feature engineering
