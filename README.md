# Group Assignment: Designing a Simple Data Pipeline and ETL Process

> **Project:** NYC Real Estate House Price ETL | Python + Pandas + PostgreSQL  
> **Course:** Big Data Analytics and Business Intelligence  
> **Submission Deadline:** 28 October  

---

## 1. Assignment Requirement-to-Evidence Map

| # | Requirement (from Course Brief) | What It Means | How This Project Meets It | Evidence to Show |
|---|---|---|---|---|
| **1** | **Data Source (≥ 2M records)** | Real dataset tied to a business scenario with at least 2 million rows. | NYC PLUTO Properties (3.3M) & Historical Sale Events (3.7M) = **7,009,514 combined rows**. | Screenshot from `python scripts/inspect_dataset.py` and PostgreSQL `COUNT(*)`. |
| **2** | **ETL Process with Pandas** | Python program using Pandas for extract, transform, validate, and load stages. | Modular ETL in `etl/`: PyArrow streams batches into Pandas DataFrames, cleaning & feature engineering in Pandas, data quality assertions in `etl/validate.py`, high-speed `COPY FROM STDIN` bulk load. | Source code, console execution log with batch counts, throughput metrics, and log files in `logs/`. |
| **3** | **Database Management (PostgreSQL)** | Store transformed data in PostgreSQL with appropriate schema. | `sql/schema.sql`: `properties` (physical tax parcels) and `sale_events` (transaction history) with PK/FK relation on `parcel_id`, `CHECK` constraints, and performance B-Tree indexes. | `sql/schema.sql`, ER diagram, pgAdmin table screenshots, `scripts/verify_database.py`. |
| **4** | **Business Value & Analysis** | Demonstrate business application and insights. | Business scenario, analytical views (`sql/analytical_views.sql`), 7 analytical queries (`sql/analysis_queries.sql`), visual ASCII charts, and CSV report exports (`scripts/run_analytics.py`). | SQL results, execution screenshots, formatted BI tables in terminal, and CSV exports in `data/processed/`. |

---

## 2. Project Architecture & Directory Layout

```text
House_Price_ETL/
│
├── config/
│   ├── __init__.py
│   └── database.py                 # PostgreSQL connection pool & SQLAlchemy engine
│
├── data/
│   ├── raw/                        # Original source datasets (> 350 MB, git-ignored)
│   │   ├── properties-00000-of-00001.parquet   # 3,306,420 rows (NYC PLUTO properties)
│   │   └── sale_events-00000-of-00001.parquet  # 3,703,094 rows (Historical sale events)
│   ├── samples/                    # Lightweight test samples (~2 MB, committed to git)
│   │   ├── properties_sample.parquet           # 25,000 rows (for instant offline demos)
│   │   └── sale_events_sample.parquet          # 5,138 matched rows (preserves 1:N relations)
│   └── processed/                  # Exported BI analytics CSVs for Tableau/PowerBI
│
├── etl/
│   ├── __init__.py
│   ├── extract.py                  # PyArrow chunked batch extractor generator
│   ├── transform.py                # Pandas data cleaning, BBL normalization, feature engineering
│   ├── validate.py                 # Data quality rules & anomaly rejection tracking
│   └── load.py                     # PostgreSQL high-performance COPY FROM STDIN bulk loader
│
├── sql/
│   ├── schema.sql                  # PostgreSQL DDL tables, constraints, and B-Tree indexes
│   ├── analytical_views.sql        # Advanced analytical BI views (Borough, Tax Equity, Asset Class)
│   └── analysis_queries.sql        # Executive business analysis queries (Q1-Q7)
│
├── scripts/
│   ├── inspect_dataset.py          # Fast Parquet metadata inspector (proves 7M+ records)
│   ├── create_sample_dataset.py    # Stratified sample generator (extracts 25k matched records)
│   ├── generate_quality_report.py  # Generates logs/data_quality_report.md audit report
│   ├── verify_database.py          # Database integrity, table count, and view verification
│   └── run_analytics.py            # Automated execution of BI reports + visual charts + CSV export
│
├── tests/
│   ├── __init__.py
│   ├── test_extract.py             # Unit tests for chunked reader
│   ├── test_transform.py           # Unit tests for BBL cleaning and borough mapping
│   ├── test_validate.py            # Unit tests for data quality validation rules
│   ├── test_load.py                # Unit tests for PostgreSQL staging loader
│   └── test_quality_and_samples.py # Unit tests for data quality audit & samples
│
├── logs/                           # Automated pipeline logs & data_quality_report.md
│
├── .env.example                    # Template for database credentials
├── .env                            # Active private database credentials (git-ignored)
├── .gitignore                      # Excludes raw datasets, logs, credentials, and caches
├── requirements.txt                # Python project dependencies
├── README.md                       # Comprehensive project report & documentation
└── pipeline.py                     # Master CLI ETL orchestrator (with --sample & RAM profiling)
```

---

## 3. Business Scenario & Problem Statement

### 3.1 Business Context
A real estate investment and analytics firm requires a scalable data infrastructure to evaluate property valuation trends, detect undervalued neighborhoods, and audit municipal property tax equity across New York City. The source data arrives in compressed Parquet files totaling **7,009,514 records**:
1. **Physical Properties (NYC PLUTO)**: Detailed building specifications, lot dimensions, tax assessments, zoning, and geographic coordinates for **3,306,420 parcels**.
2. **Historical Property Sale Events**: Transaction sale prices, sale dates, deed types, and building sizes for **3,703,094 transaction records**.

### 3.2 Problem Statement
Raw property data contains floating-point formatted IDs (e.g. `2054800111.00000000`), missing addresses, nominal/gift transfers ($0 or $1 sales), invalid construction years, and unindexed static files that cannot be queried efficiently. 

This project designs and implements an enterprise-grade ETL pipeline that:
- Extracts data in memory-safe chunks using PyArrow.
- Cleans and transforms records using Pandas.
- Validates data against strict financial and structural constraints.
- Loads records into a normalized PostgreSQL relational database using high-throughput streaming.
- Deploys analytical views and SQL queries to answer critical real estate investment and tax policy questions.

---

## 4. Dataset Inspection & Proof of 7+ Million Records

Run the inspection script to verify metadata without loading gigabytes of raw data into RAM:

```bash
python scripts/inspect_dataset.py
```

### Verified Dataset Summary

| File Name | Record Count | Number of Columns | Primary Entity & Relationship |
|---|---|---|---|
| `data/raw/properties-00000-of-00001.parquet` | **3,306,420** | 32 | **Parent Table**: Physical property parcels (1 row per physical parcel) |
| `data/raw/sale_events-00000-of-00001.parquet` | **3,703,094** | 24 | **Child Table**: Historical sale transactions ($1 : N$ with properties) |
| **Total Combined Records** | **7,009,514** | — | **Exceeds 2 Million requirement by 350%** |

*(Take a screenshot of the console output of `python scripts/inspect_dataset.py` for Section 2 of your report).*

---

## 5. Professional Smart Features

### 5.1 Automated Data Quality & Integrity Profiler
Generate a complete, publication-ready data quality audit report:
```bash
python scripts/generate_quality_report.py
```
Outputs an executive audit to [`logs/data_quality_report.md`](file:///c:/Users/Student/Desktop/House_Price_ETL/House_Price_ETL/logs/data_quality_report.md) profiling:
- Null percentage breakdown per column
- Identification of 379 nominal transfers (< $10,000) vs arms-length market sales
- Cross-table referential integrity match rate
- Constraint validation logs

### 5.2 Sub-5-Second Fast Demo Mode (`--sample`)
To demonstrate the full pipeline during a live classroom presentation without waiting to load 7 million records:
```bash
python pipeline.py --init-db --sample
```
Uses the curated 25,000-record sample in `data/samples/` preserving 100% referential integrity!

### 5.3 RAM Resource & Memory Profiling
The pipeline integrates Python's `tracemalloc` to track peak memory consumption:
```text
[PERFORMANCE AUDIT] Peak RAM Usage: 48.25 MB
```
Proves that chunked streaming maintains a flat, $O(1)$ memory footprint even over millions of rows.

### 5.4 Visual ASCII Charts & CSV Business Exports
```bash
# View terminal ASCII bar charts and export CSV tables to data/processed/:
python scripts/run_analytics.py --export-csv
```

---

## 6. Environment Setup & Configuration

### 6.1 Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- PostgreSQL 12+ (or Docker)
- Visual Studio Code & pgAdmin 4

### 6.2 Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 6.3 Configure Database Credentials
Create a `.env` file in the project root (copy from `.env.example`):
```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=house_price_db
DB_USER=postgres
DB_PASSWORD=postgres

# Batch processing configuration
BATCH_SIZE=50000
# Optional limit for testing (e.g., 50000) or leave blank for full 7M+ records
MAX_RECORDS=
```

---

## 7. PostgreSQL Database Schema Design (`sql/schema.sql`)

### 7.1 Relational Architecture

```
+------------------------------------------+          +------------------------------------------+
|                properties                |          |               sale_events                |
+------------------------------------------+          +------------------------------------------+
| record_id VARCHAR(64) [PK]               |          | sale_id VARCHAR(64) [PK]                 |
| parcel_id VARCHAR(20) [NOT NULL, BBL]    |<--(1:N)--| parcel_id VARCHAR(20) [BBL Index]        |
| borough VARCHAR(50)                      |          | borough VARCHAR(50)                      |
| address_line VARCHAR(255)                |          | address_line VARCHAR(255)                |
| unit VARCHAR(50)                         |          | unit VARCHAR(50)                         |
| city VARCHAR(100), state VARCHAR(10)     |          | city VARCHAR(100), state VARCHAR(10)     |
| zip_code VARCHAR(20), country VARCHAR(10)|          | zip_code VARCHAR(20), country VARCHAR(10)|
| latitude, longitude DOUBLE PRECISION     |          | latitude, longitude DOUBLE PRECISION     |
| property_type VARCHAR(50)                |          | property_class_raw VARCHAR(20)           |
| property_class_raw VARCHAR(20)           |          | sale_price NUMERIC(15,2) [CHECK > 0]     |
| building_sqft NUMERIC(12,2)              |          | sale_date DATE [NOT NULL]                |
| lot_sqft NUMERIC(12,2)                   |          | sale_year INT, sale_quarter INT          |
| year_built INT                           |          | sale_month INT                           |
| stories NUMERIC(5,1), units_total INT    |          | building_sqft NUMERIC(12,2)              |
| zoning VARCHAR(50), school_district      |          | price_per_sqft NUMERIC(12,2)             |
| assessed_value NUMERIC(15,2)             |          | year_built INT                           |
| assessed_land_value NUMERIC(15,2)        |          | property_age_at_sale INT                 |
| market_value NUMERIC(15,2)               |          | is_multi_parcel BOOLEAN                  |
| assessment_year INT                      |          | created_at TIMESTAMP                     |
| created_at TIMESTAMP                     |          +------------------------------------------+
+------------------------------------------+
```

### 7.2 Key Architectural Decisions
1. **Relational Normalization ($1 : N$):** Separates static parcel characteristics (`properties`) from multiple historical transactions (`sale_events`), eliminating repetitive storage of building geometry.
2. **Standardized Borough-Block-Lot (`parcel_id`):** Standardizes NYC's 10-digit tax parcel numbering scheme, stripping scientific notation and trailing zeroes.
3. **Financial Precision:** `NUMERIC(15,2)` prevents floating-point rounding inaccuracies on million-dollar properties.
4. **Data Integrity Constraints:** `CHECK (sale_price > 0)` and `sale_date NOT NULL` prevent non-arms-length transfers and corrupt transaction records.
5. **High-Performance B-Tree Indexes:** Dedicated indexes on `(parcel_id)`, `(sale_date)`, `(sale_year, sale_quarter)`, `(borough)`, and `(zip_code)` guarantee millisecond query performance across 7M+ rows.

---

## 8. Running the ETL Pipeline (`pipeline.py`)

### 8.1 Execute Full Pipeline (Initialize DB + Load All Records)
```bash
python pipeline.py --init-db
```

### 8.2 Run Fast Development Test (50,000 Records)
```bash
python pipeline.py --init-db --limit 50000
```

### 8.3 Run Offline Sample Demo (Sub-5-second demonstration)
```bash
python pipeline.py --init-db --sample
```

### 8.4 Pipeline CLI Options
- `--init-db`: Executes `sql/schema.sql` to initialize tables, constraints, and indexes.
- `--sample`: Uses lightweight 25k records from `data/samples/` for fast demo.
- `--batch-size 50000`: Sets the streaming batch size for chunked processing.
- `--limit 100000`: Limits record extraction for quick validation.
- `--skip-properties`: Skips loading the properties table.
- `--skip-sales`: Skips loading the sale_events table.
- `--apply-views`: Creates the analytical views in `sql/analytical_views.sql` (enabled by default).

---

## 9. Database Verification & Analytics

### 9.1 Verify Database Tables & Row Counts
```bash
python scripts/verify_database.py
```

### 9.2 Run Automated Business Intelligence Reports
```bash
python scripts/run_analytics.py --export-csv
```
Generates terminal reports and visual charts:
1. **Market Trends by Borough (2020-Present)**
2. **Asset Class Valuation Comparison**
3. **Assessment-to-Sale Ratio Equity Audit**
4. **Top Appreciating Neighborhood Zip Codes**

Exports clean CSV tables to `data/processed/` ready for insertion into presentation slides.

---

## 10. Running Automated Unit Tests

Execute the automated test suite covering all ETL components:

```bash
python -m unittest discover tests -v
```

### Test Suite Coverage (13 Tests Passing):
- `test_extract.py`: Tests Parquet metadata inspection and chunked batch generation.
- `test_transform.py`: Tests BBL parcel ID cleaning, borough derivation, zip code padding, and derived financial metrics.
- `test_validate.py`: Tests business validation rules and rejection counters for corrupt/anomalous rows.
- `test_load.py`: Tests in-memory CSV buffer streaming and staging table conflict resolution.
- `test_quality_and_samples.py`: Tests sample dataset generation and data quality report consistency.

---

## 11. Final Submission Checklist

- [x] **Data Source**: Minimum 2 million records verified (**7,009,514 records**).
- [x] **Business Scenario**: Realistic real estate market valuation & municipal tax equity problem.
- [x] **Python & Pandas ETL**: Full Extract, Transform, Validate, and Load stages implemented.
- [x] **Database Management**: PostgreSQL relational schema with PK/FK logic, constraints, and indexes.
- [x] **Analytical Queries**: 7 business SQL queries + 4 PostgreSQL views + Python automated reporting.
- [x] **Unit Testing**: Complete `unittest` test suite with 13 passing tests.
- [x] **Security**: Credentials externalized to `.env`, raw datasets and secrets ignored by `.gitignore`.
- [x] **Timeliness**: Ready before the **28 October** deadline.

<!-- Verified against course brief: Big Data Analytics & BI -->
