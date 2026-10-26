-- ============================================================================
-- NYC REAL ESTATE DATA PIPELINE & ETL - DATABASE SCHEMA
-- Target Database: PostgreSQL 12+
-- Datasets: NYC PLUTO Property Records & NYC Historical Property Sale Events
-- Total Records: ~7,009,514 rows (3.3M properties + 3.7M sale events)
-- ============================================================================

-- Drop existing tables if needed (cascade to clean views & constraints)
DROP TABLE IF EXISTS sale_events CASCADE;
DROP TABLE IF EXISTS properties CASCADE;

-- ----------------------------------------------------------------------------
-- 1. PROPERTIES TABLE (Tax assessment, building specifications, lot geography)
-- ----------------------------------------------------------------------------
CREATE TABLE properties (
    record_id VARCHAR(64) PRIMARY KEY,
    parcel_id VARCHAR(20) NOT NULL,
    borough VARCHAR(50),
    address_line VARCHAR(255),
    unit VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(10),
    zip_code VARCHAR(20),
    country VARCHAR(10) DEFAULT 'US',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    property_type VARCHAR(50),
    property_class_raw VARCHAR(20),
    building_sqft NUMERIC(12, 2),
    lot_sqft NUMERIC(12, 2),
    year_built INT,
    stories NUMERIC(5, 1),
    units_total INT,
    zoning VARCHAR(50),
    school_district VARCHAR(50),
    assessed_value NUMERIC(15, 2),
    assessed_land_value NUMERIC(15, 2),
    market_value NUMERIC(15, 2),
    assessment_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Comments explaining domain logic
COMMENT ON TABLE properties IS 'NYC PLUTO property records containing building specs, zoning, and tax assessments';
COMMENT ON COLUMN properties.parcel_id IS 'Standardized 10-digit Borough-Block-Lot (BBL) identifier';

-- ----------------------------------------------------------------------------
-- 2. SALE_EVENTS TABLE (Historical transaction events and sale metrics)
-- ----------------------------------------------------------------------------
CREATE TABLE sale_events (
    sale_id VARCHAR(64) PRIMARY KEY,
    parcel_id VARCHAR(20),
    borough VARCHAR(50),
    address_line VARCHAR(255),
    unit VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(10),
    zip_code VARCHAR(20),
    country VARCHAR(10) DEFAULT 'US',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    property_class_raw VARCHAR(20),
    sale_price NUMERIC(15, 2) NOT NULL,
    sale_date DATE NOT NULL,
    sale_year INT NOT NULL,
    sale_quarter INT NOT NULL,
    sale_month INT NOT NULL,
    building_sqft NUMERIC(12, 2),
    price_per_sqft NUMERIC(12, 2),
    year_built INT,
    property_age_at_sale INT,
    is_multi_parcel BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE sale_events IS 'NYC historical property sales transactions with feature-engineered pricing metrics';
COMMENT ON COLUMN sale_events.price_per_sqft IS 'Engineered metric: sale_price divided by building_sqft';
COMMENT ON COLUMN sale_events.property_age_at_sale IS 'Engineered metric: sale_year minus year_built';

-- ----------------------------------------------------------------------------
-- 3. PERFORMANCE INDEXES (Optimized for filtering, joins, and aggregations)
-- ----------------------------------------------------------------------------
CREATE INDEX idx_properties_parcel_id ON properties(parcel_id);
CREATE INDEX idx_properties_borough_zip ON properties(borough, zip_code);
CREATE INDEX idx_properties_property_type ON properties(property_type);

CREATE INDEX idx_sales_parcel_id ON sale_events(parcel_id);
CREATE INDEX idx_sales_date ON sale_events(sale_date);
CREATE INDEX idx_sales_borough_year ON sale_events(borough, sale_year);
CREATE INDEX idx_sales_price ON sale_events(sale_price);
