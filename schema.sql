-- ============================================================================
-- Section 8: PostgreSQL Schema Design (schema.sql)
-- Group Assignment: Designing a Simple Data Pipeline and ETL Process
-- ============================================================================

-- Clean rerun: Drop tables if they already exist
DROP TABLE IF EXISTS sale_events CASCADE;
DROP TABLE IF EXISTS properties CASCADE;

-- ----------------------------------------------------------------------------
-- 1. PARENT TABLE: properties (One row per physical property)
-- ----------------------------------------------------------------------------
CREATE TABLE properties (
    property_id VARCHAR(64) PRIMARY KEY,
    property_type VARCHAR(60),
    city VARCHAR(120),
    state VARCHAR(60),
    zip_code VARCHAR(20),
    building_sqft NUMERIC(12, 2),
    lot_sqft NUMERIC(12, 2),
    year_built INT,
    bedrooms NUMERIC(5, 1),
    assessed_value NUMERIC(15, 2)
);

-- ----------------------------------------------------------------------------
-- 2. CHILD TABLE: sale_events (One row per sale transaction)
-- ----------------------------------------------------------------------------
CREATE TABLE sale_events (
    sale_id BIGSERIAL PRIMARY KEY,
    property_id VARCHAR(64) NOT NULL REFERENCES properties(property_id),
    sale_date DATE,
    sale_price NUMERIC(14, 2) CHECK (sale_price > 0),
    building_sqft NUMERIC(12, 2),
    year_built INT
);

-- ----------------------------------------------------------------------------
-- 3. INDEXES: Speed up joins, filtering, and time-series queries
-- ----------------------------------------------------------------------------
CREATE INDEX idx_sales_property ON sale_events(property_id);
CREATE INDEX idx_sales_date ON sale_events(sale_date);
CREATE INDEX idx_prop_state ON properties(state);
CREATE INDEX idx_prop_city ON properties(city);
