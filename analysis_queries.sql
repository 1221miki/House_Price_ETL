-- ============================================================================
-- Section 9.3: Business Analysis Queries (analysis_queries.sql)
-- Group Assignment: Designing a Simple Data Pipeline and ETL Process
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Q1: Average sale price overall
-- Business Purpose: Establishes the baseline benchmark for the housing market.
-- ----------------------------------------------------------------------------
SELECT ROUND(AVG(sale_price), 2) AS avg_price 
FROM sale_events;

-- ----------------------------------------------------------------------------
-- Q2: Average price and volume by property type
-- Business Purpose: Guides buyers and investors on asset class valuation.
-- ----------------------------------------------------------------------------
SELECT 
    p.property_type, 
    COUNT(*) AS sales, 
    ROUND(AVG(s.sale_price), 2) AS avg_price
FROM sale_events s 
JOIN properties p ON p.property_id = s.property_id
GROUP BY p.property_type 
ORDER BY avg_price DESC;

-- ----------------------------------------------------------------------------
-- Q3: Top 10 cities / states by number of sales
-- Business Purpose: Identifies high-liquidity geographic markets.
-- ----------------------------------------------------------------------------
SELECT 
    p.city,
    p.state, 
    COUNT(*) AS sales,
    ROUND(AVG(s.sale_price), 2) AS avg_price
FROM sale_events s 
JOIN properties p ON p.property_id = s.property_id
GROUP BY p.city, p.state 
ORDER BY sales DESC 
LIMIT 10;

-- ----------------------------------------------------------------------------
-- Q4: Price trend by year
-- Business Purpose: Evaluates annual price appreciation and market inflation.
-- ----------------------------------------------------------------------------
SELECT 
    EXTRACT(YEAR FROM sale_date) AS yr, 
    COUNT(*) AS sales,
    ROUND(AVG(sale_price), 2) AS avg_price
FROM sale_events 
WHERE sale_date IS NOT NULL
GROUP BY yr 
ORDER BY yr;

-- ----------------------------------------------------------------------------
-- Q5: Properties sold more than once
-- Business Purpose: Tracks repeat sales, holding periods, and flip appreciation.
-- ----------------------------------------------------------------------------
SELECT 
    property_id, 
    COUNT(*) AS times_sold, 
    MIN(sale_price) AS lowest, 
    MAX(sale_price) AS highest,
    ROUND(MAX(sale_price) - MIN(sale_price), 2) AS appreciation
FROM sale_events 
GROUP BY property_id 
HAVING COUNT(*) > 1
ORDER BY times_sold DESC 
LIMIT 20;
