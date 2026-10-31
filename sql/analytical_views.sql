-- ============================================================================
-- NYC REAL ESTATE DATA PIPELINE - BUSINESS INTELLIGENCE & ANALYTICAL VIEWS
-- ============================================================================

-- Drop views if exist
DROP VIEW IF EXISTS v_market_summary_by_borough_year CASCADE;
DROP VIEW IF EXISTS v_assessment_vs_market_price CASCADE;
DROP VIEW IF EXISTS v_property_type_performance CASCADE;
DROP VIEW IF EXISTS v_top_appreciated_zip_codes CASCADE;

-- ----------------------------------------------------------------------------
-- View 1: Annual Market Summary by Borough
-- Business Value: Tracks volume, median price, and price/sqft trends across NYC
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_market_summary_by_borough_year AS
SELECT 
    borough,
    sale_year,
    COUNT(*) AS total_transactions,
    ROUND(AVG(sale_price), 2) AS avg_sale_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price)::NUMERIC, 2) AS median_sale_price,
    ROUND(AVG(price_per_sqft), 2) AS avg_price_per_sqft,
    ROUND(SUM(sale_price) / 1000000.0, 2) AS total_volume_millions
FROM sale_events
WHERE sale_price >= 10000 -- Filter nominal transfers
GROUP BY borough, sale_year
ORDER BY sale_year DESC, total_transactions DESC;

-- ----------------------------------------------------------------------------
-- View 2: Assessment Ratio vs. Market Transaction Price
-- Business Value: Audits tax equity by computing Sales-to-Assessment ratio
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_assessment_vs_market_price AS
SELECT 
    s.sale_id,
    s.parcel_id,
    s.borough,
    s.address_line,
    p.property_type,
    s.sale_date,
    s.sale_price,
    p.assessed_value,
    p.market_value,
    ROUND(s.sale_price / NULLIF(p.assessed_value, 0), 2) AS sale_to_assessed_ratio,
    s.price_per_sqft
FROM sale_events s
INNER JOIN properties p ON s.parcel_id = p.parcel_id
WHERE s.sale_price >= 50000 AND p.assessed_value > 0;

-- ----------------------------------------------------------------------------
-- View 3: Performance & Valuation by Property Type
-- Business Value: Guides real estate investors comparing asset classes
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_property_type_performance AS
SELECT 
    COALESCE(p.property_type, 'unclassified') AS property_type,
    COUNT(s.sale_id) AS total_sales,
    ROUND(AVG(s.sale_price), 2) AS avg_sale_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.sale_price)::NUMERIC, 2) AS median_sale_price,
    ROUND(AVG(s.price_per_sqft), 2) AS avg_price_per_sqft,
    ROUND(AVG(s.property_age_at_sale), 1) AS avg_property_age
FROM sale_events s
LEFT JOIN properties p ON s.parcel_id = p.parcel_id
WHERE s.sale_price >= 10000
GROUP BY COALESCE(p.property_type, 'unclassified')
ORDER BY total_sales DESC;

-- ----------------------------------------------------------------------------
-- View 4: Top High-Value Zip Codes
-- Business Value: Identifies the most valuable micro-markets in NYC
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_top_appreciated_zip_codes AS
SELECT 
    zip_code,
    borough,
    COUNT(*) AS total_sales,
    ROUND(AVG(sale_price), 2) AS avg_sale_price,
    ROUND(AVG(price_per_sqft), 2) AS avg_price_per_sqft,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price)::NUMERIC, 2) AS median_sale_price
FROM sale_events
WHERE zip_code IS NOT NULL 
  AND sale_price >= 10000
  AND price_per_sqft IS NOT NULL
GROUP BY zip_code, borough
HAVING COUNT(*) >= 50
ORDER BY avg_price_per_sqft DESC;

-- Analytical Views: Median calculation using PERCENTILE_CONT and volume aggregation
