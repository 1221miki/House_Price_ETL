# Group Final Submission Report: Big Data Analytics & Business Intelligence

> **Project Title:** NYC Real Estate Valuation & Transaction Data Pipeline (House Price ETL)  
> **Course:** Big Data Analytics and Business Intelligence  
> **Architecture:** Python (PyArrow + Pandas) | PostgreSQL 17 Relational Database | SQLAlchemy  
> **Submission Date:** October 2026  

---

## 1. Executive Summary & Brief Alignment

This project designs, engineers, and validates an end-to-end Enterprise Data Pipeline and Extract-Transform-Load (ETL) architecture for big data analytics. The solution satisfies and exceeds all core components mandated by the course brief:

| # | Course Brief Requirement | Project Implementation | Quantitative Evidence |
|---|---|---|---|
| **1** | **Data Source (≥ 2M records)** | Two interconnected datasets: NYC PLUTO Residential Properties (3.3M) and Historical NYC Property Sale Events (3.7M). | **7,009,514 total records** verified via Parquet metadata profiler. |
| **2** | **ETL Process with Pandas** | Modular chunked ETL engine: PyArrow zero-copy reader, Pandas data cleaning, BBL normalization, feature engineering, and high-throughput streaming bulk loader. | Validated in batches of 50,000 records; average throughput **~6,200 rows/second**; peak RAM **< 50 MB**. |
| **3** | **Database Management (PostgreSQL)** | Normalized Third Normal Form (3NF) relational schema with Primary Key / Foreign Key constraints, domain CHECK constraints, B-Tree indexes, and 4 analytical views. | Deployed on PostgreSQL 17 cluster with automated schema DDL and integrity verification. |
| **4** | **Business Value & Analytics** | Executive real estate analytics answering municipal tax equity, neighborhood appreciation, and asset-class price dynamics. | 4 automated analytical SQL views, terminal visual charts, and CSV report exports. |

---

## 2. Business Scenario & Problem Statement

### 2.1 Business Context
Municipal governments, mortgage lenders, and institutional real estate investment trusts (REITs) require reliable data infrastructures to monitor market valuations, assess tax equity, and forecast neighborhood appreciation across New York City. 

The source data originates from two foundational municipal datasets:
1. **NYC Primary Land Use Tax Lot Output (PLUTO)**: Physical specifications, building dimensions, zoning codes, and assessed valuations for **3,306,420 physical parcels**.
2. **NYC Department of Finance Automated City Register Information System (ACRIS)**: Historical deed transfers, transaction dates, and market sale prices for **3,703,094 sale events**.

### 2.2 Business Problems Solved
Raw municipal data exhibits severe data quality anomalies that prevent direct business querying:
* **Floating-Point Identifier Corruption:** NYC 10-digit Borough-Block-Lot (BBL) parcel identifiers arrive formatted as float strings (e.g. `2054800111.00000000`), breaking table joins.
* **Non-Arms-Length Transactions:** Over 350 transactions in sample audits reflect nominal $0 or $1 sales (deed corrections or intra-family gifts) that distort market price averages.
* **Corrupt Physical Attributes:** Negative square footage, invalid construction years (e.g. year 0 or future years), and missing borough names.
* **Memory Constraints:** Static raw files total >350 MB compressed and >3 GB in uncompressed RAM. Inexperienced pipelines trigger Out-Of-Memory (OOM) crashes on student machines.

---

## 3. Data Pipeline & ETL Architecture

The pipeline follows a decoupled 4-stage architecture designed for constant memory footprint (O(1) space complexity):
1. **Extract Stage (PyArrow):** Memory-efficient generator streaming batches of 50,000 records from uncompressed Parquet without RAM saturation.
2. **Transform Stage (Pandas):** BBL parcel ID normalization, borough geographic derivation, timestamp parsing, and derived financial metrics (`price_per_sqft` and `property_age_at_sale`).
3. **Validate Stage:** Enforces business logic assertions (positive price, plausible construction year, non-null IDs) and isolates anomalies.
4. **Load Stage (PostgreSQL COPY):** Direct in-memory buffer streaming into PostgreSQL using `COPY FROM STDIN` rather than slow individual `INSERT` statements.
5. **Analytics & BI Stage:** Materialized views, analytical queries, and automated CSV report generation.

---

## 4. Relational Database Schema Design (PostgreSQL)

The database schema eliminates redundancy by separating physical real estate assets from dynamic financial transactions through a strict **1 : N (One-to-Many)** relational model:
* **`properties` (Parent Table):** Primary Key `record_id`, indexed business key `parcel_id`. Stores building dimensions, zoning, tax assessments, and geographic coordinates.
* **`sale_events` (Child Table):** Primary Key `sale_id`, Foreign Key `parcel_id` referencing properties. Stores transaction prices, deed types, and sale dates with `CHECK (sale_price > 0)` constraints.

### 4.1 Indexing & Performance Strategy
Dedicated B-Tree indexes maintain millisecond query speeds across multi-million rows:
* `idx_properties_parcel_id` & `idx_sales_parcel_id`: Optimizes high-speed relational joins.
* `idx_sales_date` & `idx_sales_borough_year`: Accelerates time-series and annual summaries.
* `idx_sales_price`: Enhances arms-length transaction filtering.
* `idx_properties_borough_zip`: Accelerates geographic aggregations.

---

## 5. Automated Data Quality Audit

An automated audit executed on raw sample batches (`logs/data_quality_report.md`) revealed:
* **Total Records Audited:** 7,009,514 rows.
* **BBL Key Cleanliness:** 100% normalized using regex stripping of `.00000000` float artifacts.
* **Nominal Transfers:** 379 records (< $10,000) isolated to prevent distortion of market trends.
* **Null Handling:** Primary identifiers and addresses verified at 99.99%+ completeness.

---

## 6. Business Intelligence & Empirical Findings

Executing `scripts/run_analytics.py --export-csv` yielded key insights:
* **Median Property Valuation by Borough:** Brooklyn and Manhattan lead median prices ($640,000 to $1,130,000) at $490–$500/sqft. The Bronx provides the most accessible entry point ($300–$340/sqft).
* **Asset Class Dynamics:** Multi-family properties dominate transaction density in urban corridors ($734k avg), while mixed-use and commercial developments reach $2.5M–$2.9M.
* **Tax Equity Discrepancy:** Outer-borough single-family homes bear higher effective assessment-to-market ratios compared to prime Manhattan luxury assets.

---

## 7. Submission Evidence Checklist

- [x] **Proof of Scale:** Console output of `inspect_dataset.py` proving **7,009,514 Parquet records**.
- [x] **Proof of ETL Execution:** Batch streaming logs demonstrating continuous throughput of **~6,200 rows/second**.
- [x] **Proof of Database Management:** PostgreSQL 17 database verified with active tables, PK/FK relationships, and B-Tree indexes.
- [x] **Proof of Analytical Depth:** 4 active analytical SQL views and exported BI CSVs in `Data/processed/`.
- [x] **Proof of Code Quality:** 13/13 automated unit tests passing in `tests/`.
- [x] **Security & Best Practices:** Password credentials isolated in `.env` with URL encoding for special characters.

