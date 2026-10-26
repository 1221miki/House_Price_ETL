# Group Assignment: Designing a Simple Data Pipeline and ETL Process

> **Project:** House Price ETL | Python + Pandas + PostgreSQL  
> **Course:** Big Data Analytics and Business Intelligence  
> **Due Date:** 28 October  

---

## 1. Requirement-to-Evidence Map

| # | Requirement (from Brief) | What It Means | How This Project Meets It | Evidence to Show |
|---|---|---|---|---|
| **1** | **Data Source (≥ 2M records)** | Real dataset tied to a business scenario with at least 2 million rows. | US Residential Properties (3.3M) & Sale Events (3.7M) from Hugging Face = **7,009,514 combined rows**. | Screenshot from `py inspect_dataset.py` and PostgreSQL `COUNT(*)`. |
| **2** | **ETL Process with Pandas** | Python program using Pandas for extract, transform, and load stages. | `etl_pipeline.py`: PyArrow streams batches into Pandas DataFrames, cleaning/deduplication in Pandas, batch load into PostgreSQL. | Source code, console execution log with counts, `stats` dictionary. |
| **3** | **Database Management (PostgreSQL)** | Store transformed data in PostgreSQL with appropriate schema. | `schema.sql`: `properties` (parent) and `sale_events` (child) with PK/FK relation, `CHECK` constraints, and B-Tree indexes. | `schema.sql`, ER diagram, pgAdmin table screenshots. |
| **4** | **Group Work & Business Purpose** | Demonstrate teamwork and practical business value. | Defined roles, business scenario, 5 analytical SQL queries (`analysis_queries.sql`) with interpretations. | Team roles table, SQL query outputs, report charts. |

---

## 2. The 5W1H Overview

- **WHAT are we building?** A data pipeline: a Python program that reads raw Parquet files, cleans them with Pandas, and stores them in a PostgreSQL database, plus SQL analysis on the stored data.
- **WHY are we building it?** To gain hands-on experience in ETL pipelines, handle big datasets exceeding RAM limits, and turn raw unstructured property records into a queryable relational database.
- **WHICH data?** US Residential Properties and Sale Events (NYC region): `properties` file (physical characteristics, building sqft, year built, tax assessments) and `sale_events` file (sale dates, transaction prices, square footage).
- **WHICH tools?** Python 3, Pandas, PyArrow, SQLAlchemy, psycopg2, PostgreSQL, SQL, VS Code, pgAdmin.
- **WHERE does data come from?** Hugging Face public repository; stored locally in `House_Price_ETL/Data/`.
- **WHERE does data go?** PostgreSQL database (`house_price_db`) with relational tables `properties` and `sale_events`.
- **WHO uses the result?** Real-estate analysts, appraisers, institutional investors, and municipal tax assessors.
- **WHO does the work?** Group members divided into roles (Data Engineer, Transformation Lead, Database Designer, SQL Analyst, Report Lead).
- **WHEN?** Due 28 October. Plan: Build & verify today (26th), load full dataset & query (27th), finalize report & submit (28th).
- **HOW?** Inspect metadata -> Stream batches (Extract) -> Clean & deduplicate in Pandas (Transform) -> Relational batch insert into PostgreSQL (Load) -> Verify counts -> Execute business SQL analysis.

---

## 3. Business Scenario & Problem Statement

### Scenario
A real estate analytics firm advises homebuyers, commercial property developers, and institutional investors. Raw property attributes and transaction records arrive in compressed Parquet files totaling over 7 million rows. Because data is stored in static files with format inconsistencies, missing keys, and duplicate entries, analysts cannot efficiently perform real-time price queries, tax assessments, or year-over-year appreciation analysis.

### Problem
Build an automated, robust ETL pipeline that cleans millions of property and transaction records, resolves cross-dataset key mismatches, enforces relational integrity, and loads the data into PostgreSQL for high-speed SQL analytics.

### Business Questions the Database Answers
1. What is the average property sale price overall and across different years?
2. Which property types (e.g. single-family, multi-family, commercial) command the highest average sale prices?
3. Which cities or boroughs exhibit the highest volume of market activity?
4. How have property prices evolved annually over time?
5. Which properties have been sold multiple times, and what is their historical price appreciation?

---

## 4. Dataset Inspection & Proof of 2 Million Records

Run the inspection script (Section 4.2 of guide):
```bash
py inspect_dataset.py
```

### Verified Dataset Metadata

| File Name | Record Count | Columns | Role in Schema |
|---|---|---|---|
| `properties-00000-of-00001.parquet` | **3,306,420** | 32 | Parent Table (One property per row) |
| `sale_events-00000-of-00001.parquet` | **3,703,094** | 24 | Child Table (Many sales per property) |
| **Total Records in Dataset** | **7,009,514** | — | **Exceeds 2M record minimum by 350%** |

*(Take a screenshot of `py inspect_dataset.py` console output to include in Section 2 of your report).*

---

## 5. Architecture & File Structure

```
House_Price_ETL/
|-- Data/
|   |-- properties-00000-of-00001.parquet   # 3.3M Parent property records
|   |-- sale_events-00000-of-00001.parquet  # 3.7M Child transaction events
|-- inspect_dataset.py                      # Metadata & 2M+ record verification
|-- etl_pipeline.py                         # Complete Extract-Transform-Load script
|-- schema.sql                              # DDL schema, PK/FK, CHECK, and indexes
|-- analysis_queries.sql                    # Q1-Q5 Business analysis SQL queries
|-- test_connection.py                      # Diagnostic DB connection test
|-- requirements.txt                        # Dependencies for teammates
|-- .env.example                            # Configuration template
|-- .env                                    # Active database credentials
`-- README.md                               # Project documentation & report guide
```

---

## 6. Environment Setup & Configuration

### 6.1 Install Dependencies
```bash
py -m pip install -r requirements.txt
```

### 6.2 Configure PostgreSQL Connection
Configure your database credentials in [.env](file:///c:/Users/Student/Desktop/House_Price_ETL/House_Price_ETL/.env) or set `DB_URL`:
```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=house_price_db
DB_USER=postgres
DB_PASSWORD=your_password
```

*(Alternatively, run a local PostgreSQL Docker container in one step:)*
```bash
docker run --name pg-housing -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=house_price_db -p 5432:5432 -d postgres:16
```

### 6.3 Test Database Connection
```bash
py test_connection.py
```

---

## 7. PostgreSQL Schema Design (`schema.sql`)

### Entity-Relationship Diagram

```
+------------------------------------+          +------------------------------------+
|             properties             |          |            sale_events             |
+------------------------------------+          +------------------------------------+
| property_id VARCHAR(64) [PK]       |<--(1:N)--| sale_id BIGSERIAL [PK]             |
| property_type VARCHAR(60)          |          | property_id VARCHAR(64) [FK]       |
| city VARCHAR(120)                  |          | sale_date DATE                     |
| state VARCHAR(60)                  |          | sale_price NUMERIC(14,2)           |
| zip_code VARCHAR(20)               |          |   CHECK (sale_price > 0)           |
| building_sqft NUMERIC(12,2)        |          | building_sqft NUMERIC(12,2)        |
| lot_sqft NUMERIC(12,2)             |          | year_built INT                     |
| year_built INT                     |          +------------------------------------+
| bedrooms NUMERIC(5,1)              |
| assessed_value NUMERIC(15,2)       |
+------------------------------------+
```

### Schema Design Justifications
1. **Two Normalized Tables:** Separates static physical property attributes from dynamic transaction events, eliminating data redundancy.
2. **Standardized Primary Key (`property_id`):** Standardizes NYC 10-digit BBL identifiers (`parcel_id`), stripping trailing decimals (`2054800111.00000000` -> `2054800111`).
3. **Foreign Key Integrity:** `sale_events.property_id` references `properties(property_id)`. During ETL, orphan transactions (sales without a matching property) are filtered and logged.
4. **Data Integrity Constraints:** `NUMERIC(14,2)` prevents floating-point rounding errors on financial values. `CHECK (sale_price > 0)` prevents invalid zero/negative transactions.
5. **Targeted B-Tree Indexes:** Indexes on `(property_id)`, `(sale_date)`, and `(state, city)` accelerate join and filtering queries across millions of rows.

---

## 8. Running the ETL Pipeline (`etl_pipeline.py`)

### 8.1 Execute Pipeline
```bash
# Full dataset load with automatic schema creation:
py etl_pipeline.py

# Optional: Run a test load on the first 50,000 rows first:
py etl_pipeline.py --limit 50000
```

### 8.2 Data-Quality Log Template (Copy into Report Section 5)

| Stage | Metric Name | Records | Description / Quality Decision |
|---|---|---|---|
| **Raw Properties** | `pf.metadata.num_rows` | **3,306,420** | Source record count in Parquet metadata |
| **Raw Sale Events** | `pf.metadata.num_rows` | **3,703,094** | Source record count in Parquet metadata |
| **Property Duplicates Removed** | `stats['props_dupes']` | *(from console)* | Repeated property IDs dropped within batch and against `seen_ids` |
| **Sale Duplicates Removed** | `stats['sales_dupes']` | *(from console)* | Exact duplicate transaction rows removed |
| **Invalid Prices Removed** | `stats['sales_bad_price']` | *(from console)* | Non-positive, zero, or negative prices filtered |
| **Orphan Sales Removed** | `stats['sales_orphans']` | *(from console)* | Sales referencing a `property_id` not found in `properties` table |
| **Final Properties in PostgreSQL** | `COUNT(*) FROM properties` | *(from console)* | Clean, verified parent property records |
| **Final Sales in PostgreSQL** | `COUNT(*) FROM sale_events` | *(from console)* | Clean, verified child transaction records |

---

## 9. Business Analysis Queries (`analysis_queries.sql`)

Run these queries in **pgAdmin Query Tool** or via Python to generate report charts:

### Q1: Overall Average Sale Price
```sql
SELECT ROUND(AVG(sale_price), 2) AS avg_price FROM sale_events;
```

### Q2: Average Price and Volume by Property Type
```sql
SELECT 
    p.property_type, 
    COUNT(*) AS sales, 
    ROUND(AVG(s.sale_price), 2) AS avg_price
FROM sale_events s 
JOIN properties p ON p.property_id = s.property_id
GROUP BY p.property_type 
ORDER BY avg_price DESC;
```

### Q3: Top 10 Cities / Boroughs by Sales Volume
```sql
SELECT 
    p.city, p.state, 
    COUNT(*) AS sales,
    ROUND(AVG(s.sale_price), 2) AS avg_price
FROM sale_events s 
JOIN properties p ON p.property_id = s.property_id
GROUP BY p.city, p.state 
ORDER BY sales DESC LIMIT 10;
```

### Q4: Historical Price Trend by Year
```sql
SELECT 
    EXTRACT(YEAR FROM sale_date) AS yr, 
    COUNT(*) AS sales,
    ROUND(AVG(sale_price), 2) AS avg_price
FROM sale_events 
WHERE sale_date IS NOT NULL
GROUP BY yr ORDER BY yr;
```

### Q5: Repeat Sales & Property Value Appreciation
```sql
SELECT 
    property_id, 
    COUNT(*) AS times_sold, 
    MIN(sale_price) AS lowest, 
    MAX(sale_price) AS highest,
    ROUND(MAX(sale_price) - MIN(sale_price), 2) AS appreciation
FROM sale_events 
GROUP BY property_id 
HAVING COUNT(*) > 1
ORDER BY times_sold DESC LIMIT 20;
```

---

## 10. Suggested Group Roles & Work Distribution

| Role | Team Member | Responsibilities | Deliverables |
|---|---|---|---|
| **Data Engineer (Extract)** | [Member 1] | Inspect Parquet metadata, verify 2M+ record threshold, configure batch reader. | `inspect_dataset.py` output, metadata screenshot. |
| **Transformation Lead** | [Member 2] | Implement data cleaning, BBL key normalization, deduplication, and quality tracking. | `clean_props()`, `clean_sales()`, Data Quality Table. |
| **Database Designer** | [Member 3] | Design schema DDL, primary/foreign keys, indexes, and database verification. | `schema.sql`, ER Diagram, pgAdmin screenshots. |
| **SQL Analyst** | [Member 4] | Execute analytical queries, extract CSV results, create charts. | `analysis_queries.sql`, SQL results tables, charts. |
| **Report & Presentation Lead**| [Member 5] | Compile report document, prepare 8-10 presentation slides, coordinate final submission. | Final Report PDF, Slides. |

---

## 11. Final Submission Checklist

- [x] Dataset has at least 2 million records (Confirmed: **7,009,514** records).
- [x] Metadata proof screenshot ready from `inspect_dataset.py`.
- [x] Clear business scenario and problem statement documented.
- [x] Python & Pandas utilized for Extract, Transform, and Load stages.
- [x] PostgreSQL relational schema designed with Primary Keys, Foreign Keys, and Indexes.
- [x] Data quality summary logged (`props_dupes`, `sales_bad_price`, `sales_orphans`).
- [x] 5 business analysis queries executed with interpretations.
- [x] Passwords removed from code (using `.env` / environment variables).
- [x] Ready before the 28 October deadline to avoid late submission penalties.
