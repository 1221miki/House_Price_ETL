# Group Assignment: Designing a Simple Data Pipeline and ETL Process

> **Project:** NYC Real Estate House Price ETL | Python + Pandas + PostgreSQL  
> **Course:** Big Data Analytics and Business Intelligence  
> **Instructor:** Derbew Felasman  
> **Institution:** Debre Berhan University (DBU)  
> **Submission Date:** November 2026  

---

### 👥 Project Team Members

| No. | Student Full Name | Student ID | Institution | Project Role |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Asamnew Agiz** | `DBU1601394` | Debre Berhan University | Data Engineering & Database Administration |
| **2** | **Solomon Tadese** | `DBU1601626` | Debre Berhan University | ETL Pipeline & Data Transformation |
| **3** | **Dagmawit Eshete** | `DBU1601878` | Debre Berhan University | Data Quality & Validation Rules |
| **4** | **Jemal Yimer** | `DBU1601836` | Debre Berhan University | Memory Optimization & Reporting |
| **5** | **Selamawit Tadese** | `1601596` | Debre Berhan University | Data Preparation & Quality Assurance |
| **6** | **Ehitemelak Tekle Haymanot** | `1602121` | Debre Berhan University | Data Validation & Documentation Support |

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
Outputs an executive audit to [`logs/data_quality_report.md`](logs/data_quality_report.md) profiling:
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

### 5.5 Interactive Project Guide & Dataset Preview
Generate the project overview page and open `dataset_viewer.html` in a browser:
```bash
python scripts/generate_html_viewer.py
```
The page explains the ETL workflow and the roles of Python, SQL, HTML, CSS, and JavaScript. It also provides searchable property and sale-event preview tables. Those tables contain only the preview rows; the full Parquet datasets are processed by the ETL pipeline.

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
pytest tests/ -v
# or using unittest:
python -m unittest discover tests -v
```

### Test Suite Coverage (15 Tests Passing - 100% PASS):
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
- [x] **Unit Testing**: Complete test suite with 15 passing tests in Pytest (100% PASS).
- [x] **Comprehensive Report**: 21-section technical report in `FINAL_GROUP_PROJECT_SUBMISSION_REPORT.md` (and `reports/`).
- [x] **Security**: Credentials externalized to `.env`, raw datasets and secrets ignored by `.gitignore`.
- [x] **Timeliness**: Ready before the **28 October** deadline.

<!-- Verified against course brief: Big Data Analytics & BI -->

---

## 12. Live Presentation & Defense Guide (Terminal, PostgreSQL & Visuals)

This section provides the exact demonstration flow, terminal commands, pgAdmin queries, and speaking script for presenting this project to your lecturer.

### 12.1 Primary Terminal Demonstration Flow (5 Core Commands)
Run these commands from the project root in PowerShell. The output on your terminal proves each stage of the project rubric:

| No. | Command | What It Proves / Does | Rubric Stage |
|:---:|:---|:---|:---:|
| **1** | `python inspect_dataset.py` | Scans Parquet metadata in milliseconds without RAM overload. Proves **7,009,514 raw records** (exceeds 2M requirement). | **Data Source (Rubric #1)** |
| **2** | `python scripts/verify_database.py` | Connects to PostgreSQL `house_price_db`; audits active row counts (2,050,000+), 9 B-Tree indexes, and 4 views. | **Database Management (Rubric #3)** |
| **3** | `python main.py --sample` | Executes live Extract, Transform, Validate, and Load pipeline on 25k records in < 5 seconds. | **ETL with Pandas (Rubric #2)** |
| **4** | `pytest -v` | Executes automated unit test suite. Proves **15 of 15 tests pass (100% PASS)** across all ETL modules. | **Software Quality & Validation** |
| **5** | `python scripts/run_analytics.py` | Queries analytical SQL views; prints formatted BI summary tables and ASCII price distribution charts. | **Business Analytics (Rubric #4)** |

---

### 12.2 PostgreSQL pgAdmin 4 Verification Queries
In pgAdmin 4: right-click `house_price_db` -> select **Query Tool** -> paste query -> press **F5**:

#### Query 1: Exact Record Count Verification
> **Purpose:** Proves active records loaded in both physical property and transaction tables.
```sql
SELECT 'properties' AS tbl, COUNT(*) FROM properties
UNION ALL
SELECT 'sale_events', COUNT(*) FROM sale_events;
```

#### Query 2: Relational Integrity & Foreign Key Demonstration
> **Purpose:** Proves 1-to-many relationship between property parcels and historical sales joined via `parcel_id`.
```sql
SELECT p.parcel_id, p.borough,
       s.sale_price, s.sale_date
FROM properties p
JOIN sale_events s
  ON p.parcel_id = s.parcel_id
LIMIT 10;
```

#### Query 3: Real Estate Market Analytics View
> **Purpose:** Reads the analytical BI view displaying average prices and transaction volume by borough and year.
```sql
SELECT *
FROM v_market_summary_by_borough_year
LIMIT 10;
```

---

### 12.3 Supporting & Backup Commands (Charts, Reports & UI Viewer)

Use these commands if the instructor asks for graphical charts, exported CSV reports, or custom pipeline loads:

| No. | Command | Purpose / Functionality | Output Location |
|:---:|:---|:---|:---|
| **1** | `python scripts/generate_charts.py` | Builds 5 publication-ready Matplotlib analytical charts from PostgreSQL. | `Data/processed/charts/*.png` |
| **2** | `python scripts/run_analytics.py --export-csv` | Exports analytical view results to clean CSV files for Excel / Power BI. | `Data/processed/*.csv` |
| **3** | `python scripts/generate_quality_report.py` | Profiles column nulls, key match rates, and $0 nominal transfers. | `logs/data_quality_report.md` |
| **4** | `python scripts/generate_html_viewer.py` | Rebuilds offline interactive web dashboard. | `dataset_viewer.html` |
| **5** | `python main.py --limit 10000 --skip-sales` | Runs small custom ETL batch (10,000 properties only) without sales. | Staging & PostgreSQL tables |

#### Launch Visual Artifacts During Defense:
```powershell
# Open the Borough Average Price Chart in Windows Photos:
Start-Process Data\processed\charts\chart1_borough_avg_price.png

# Open the Interactive Web Dashboard in your browser:
Start-Process dataset_viewer.html
```

> [!CAUTION]
> **LIVE DEMO WARNING:**  
> **Do NOT run `python main.py --init-db` during the live presentation!**  
> `--init-db` drops and recreates all database tables. Only use `--sample` or `--limit` to keep your existing 2,050,000 loaded records intact.

---

### 12.4 Speaker Defense Script ("What to Say to Your Lecturer")

| Demonstration Stage | Recommended Speaking Script | Key Technical Term to Emphasize |
|:---|:---|:---|
| **1. Dataset Inspection** | *"First, I verify the size and structure of our raw dataset using metadata streaming. As shown, we have 7,009,514 total records across properties and historical sales, exceeding the 2-million course requirement by 350%."* | Chunked metadata extraction, Parquet compression |
| **2. Database Verification** | *"Here, I demonstrate that the data is successfully stored in a normalized PostgreSQL relational database with 9 B-Tree performance indexes and 4 pre-aggregated analytical views."* | 3NF Normalization, B-Tree indexing, pgAdmin 4 |
| **3. ETL Execution** | *"I use Pandas to extract, transform, clean, and validate the records. In this live demo, our `--sample` flag processes 25,000 records end-to-end in under 5 seconds with zero RAM bloat."* | Generator streaming, `COPY FROM STDIN` bulk load |
| **4. Automated Testing** | *"We implemented comprehensive automated unit testing using Pytest. All 15 tests pass with 100% success rate, verifying data type coercion, BBL parcel validation, and anomaly rejection."* | Pytest, Test-Driven Quality, 100% Pass Rate |
| **5. Relational Queries** | *"These SQL queries demonstrate referential integrity: properties and sales are linked via a 10-digit standardized Borough-Block-Lot (`parcel_id`) identifier."* | Foreign Key relationship, BBL standardization |
| **6. Business Analytics** | *"Finally, our analytics provide actionable market insights. For instance, Manhattan leads with an average price of $1.89M across 491,209 sales, while outer boroughs show accelerating price appreciation."* | BI views, Tax equity audit, Valuation trends |