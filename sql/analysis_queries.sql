-- ============================================================================
-- NYC REAL ESTATE DATA PIPELINE - BUSINESS ANALYSIS QUERIES
-- Group Assignment: Designing a Simple Data Pipeline and ETL Process
-- Target: PostgreSQL Database (house_price_db)
-- Total Records: ~7,009,514 (Properties + Historical Sale Events)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Q1: Overall Market Baseline Benchmarks
-- Business Objective: Determine total transaction volume, average & median price.
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_sales_recorded,
    ROUND(AVG(sale_price), 2) AS overall_avg_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price)::NUMERIC, 2) AS overall_median_price,
    ROUND(MIN(sale_price), 2) AS min_sale_price,
    ROUND(MAX(sale_price), 2) AS max_sale_price,
    ROUND(SUM(sale_price) / 1000000000.0, 3) AS total_market_volume_billions
FROM sale_events
WHERE sale_price >= 10000;

-- ----------------------------------------------------------------------------
-- Q2: Market Performance and Liquidity by Borough
-- Business Objective: Identify which NYC boroughs drive the highest transaction
-- volume and price per square foot.
-- ----------------------------------------------------------------------------
SELECT 
    borough,
    COUNT(*) AS total_transactions,
    ROUND(AVG(sale_price), 2) AS avg_sale_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price)::NUMERIC, 2) AS median_sale_price,
    ROUND(AVG(price_per_sqft), 2) AS avg_price_per_sqft,
    ROUND(SUM(sale_price) / 1000000.0, 2) AS volume_millions
FROM sale_events
WHERE sale_price >= 10000 AND borough IS NOT NULL
GROUP BY borough
ORDER BY total_transactions DESC;

-- ----------------------------------------------------------------------------
-- Q3: Historical Annual Price Trend & Inflation Analysis
-- Business Objective: Track YoY market trajectory, volume fluctuations, and price growth.
-- ----------------------------------------------------------------------------
SELECT 
    sale_year,
    COUNT(*) AS total_sales,
    ROUND(AVG(sale_price), 2) AS avg_sale_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price)::NUMERIC, 2) AS median_sale_price,
    ROUND(AVG(price_per_sqft), 2) AS avg_price_per_sqft
FROM sale_events
WHERE sale_year BETWEEN 2000 AND 2025 AND sale_price >= 10000
GROUP BY sale_year
ORDER BY sale_year ASC;

-- ----------------------------------------------------------------------------
-- Q4: Property Type / Asset Class Valuation Comparison
-- Business Objective: Evaluate risk and pricing spreads across property categories
-- (e.g., Single Family, Condos, Multi-Family, Commercial).
-- ----------------------------------------------------------------------------
SELECT 
    COALESCE(p.property_type, 'Unclassified') AS property_type,
    COUNT(s.sale_id) AS total_sales,
    ROUND(AVG(s.sale_price), 2) AS avg_sale_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.sale_price)::NUMERIC, 2) AS median_sale_price,
    ROUND(AVG(s.price_per_sqft), 2) AS avg_price_per_sqft,
    ROUND(AVG(p.year_built), 0) AS avg_year_built
FROM sale_events s
JOIN properties p ON s.parcel_id = p.parcel_id
WHERE s.sale_price >= 10000
GROUP BY p.property_type
ORDER BY total_sales DESC;

-- ----------------------------------------------------------------------------
-- Q5: Tax Assessment Equity Analysis (Sales-to-Assessment Ratio)
-- Business Objective: Identify whether properties are systematically under-assessed
-- or over-assessed relative to actual arms-length market transactions.
-- ----------------------------------------------------------------------------
SELECT 
    s.borough,
    COUNT(*) AS sample_size,
    ROUND(AVG(s.sale_price), 2) AS avg_market_sale_price,
    ROUND(AVG(p.assessed_value), 2) AS avg_tax_assessed_value,
    ROUND(AVG(s.sale_price / NULLIF(p.assessed_value, 0)), 2) AS avg_sale_to_assessed_ratio
FROM sale_events s
JOIN properties p ON s.parcel_id = p.parcel_id
WHERE s.sale_price >= 50000 AND p.assessed_value > 0
GROUP BY s.borough
ORDER BY sample_size DESC;

-- ----------------------------------------------------------------------------
-- Q6: Top 10 Most Active Zip Codes by Transaction Liquidity
-- Business Objective: Pinpoint high-demand neighborhood micro-markets.
-- ----------------------------------------------------------------------------
SELECT 
    s.zip_code,
    s.borough,
    COUNT(*) AS total_sales,
    ROUND(AVG(s.sale_price), 2) AS avg_sale_price,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.sale_price)::NUMERIC, 2) AS median_sale_price
FROM sale_events s
WHERE s.zip_code IS NOT NULL AND s.sale_price >= 10000
GROUP BY s.zip_code, s.borough
ORDER BY total_sales DESC
LIMIT 10;

-- ----------------------------------------------------------------------------
-- Q7: Repeat Sales Analysis (Properties Sold Multiple Times)
-- Business Objective: Track turnover rates, flipping velocity, and holding duration.
-- ----------------------------------------------------------------------------
SELECT 
    parcel_id,
    COUNT(*) AS transaction_count,
    ROUND(MIN(sale_price), 2) AS first_recorded_price,
    ROUND(MAX(sale_price), 2) AS highest_recorded_price,
    ROUND(MAX(sale_price) - MIN(sale_price), 2) AS total_nominal_appreciation
FROM sale_events
WHERE parcel_id IS NOT NULL AND sale_price >= 10000
GROUP BY parcel_id
HAVING COUNT(*) >= 3
ORDER BY transaction_count DESC, total_nominal_appreciation DESC
LIMIT 20;

-- Queries designed for municipal tax equity and neighborhood appreciation analysis
