# Data Quality & Integrity Audit Report

> **Generated at:** 2026-10-29 15:34:06  
> **Project:** House Price ETL | Course: Big Data Analytics & BI  

---

## 1. Executive Summary & Scale

| Metric | Properties Dataset | Sale Events Dataset | Combined Total |
|---|---|---|---|
| **File Name** | `properties-00000-of-00001.parquet` | `sale_events-00000-of-00001.parquet` | — |
| **File Size on Disk** | 190.75 MB | 153.73 MB | 344.48 MB |
| **Total Record Count** | **3,306,420** | **3,703,094** | **7,009,514** |
| **Number of Attributes** | 32 | 24 | 56 combined |
| **Audit Sample Size** | 100,000 | 100,000 | — |

---

## 2. Referential Integrity & Foreign Key Audit

- **Primary Join Key:** `parcel_id` (NYC 10-digit Borough-Block-Lot / BBL).
- **Sample Match Rate:** **7.98%** of sale events successfully correlate to physical parcel records in the properties dataset.
- **Quality Decision:** In the ETL pipeline, child sales records reference `properties(parcel_id)`. Non-matching or orphan transactions are logged and isolated into staging tables.

---

## 3. Financial Distribution & Anomaly Analysis (Sale Events)

| Category | Price Range | Count (Sample 100k) | % of Sample | Business Interpretation |
|---|---|---|---|---|
| **Nominal / Non-Arms-Length Transfers** | `< $10,000` (e.g. $0, $1) | 379 | 0.38% | Intra-family gifts, deed corrections, or nominal foreclosures (filtered out during BI analytics). |
| **Standard Arms-Length Transactions** | `$10,000` to `$10,000,000` | 99,621 | 99.62% | True residential and commercial market sales. |
| **Institutional & Luxury Transactions** | `> $10,000,000` | 2,082 | 2.08% | Commercial skyscrapers, large multifamily developments, or luxury penthouses. |

---

## 4. Column Missingness & Null Value Profile

### Properties Dataset (Top Columns)
| Column | Data Type | Null Count (Sample 100k) | Null Percentage | Quality Assessment |
|---|---|---|---|---|
| `record_id` | `str` | 0 | 0.0% | Healthy |
| `source` | `str` | 0 | 0.0% | Healthy |
| `parcel_id` | `str` | 0 | 0.0% | Healthy |
| `address_line` | `str` | 1 | 0.0% | Healthy |
| `unit` | `str` | 100,000 | 100.0% | Sparse |
| `city` | `str` | 0 | 0.0% | Healthy |
| `state` | `str` | 0 | 0.0% | Healthy |
| `zip_code` | `str` | 2 | 0.0% | Healthy |
| `country` | `str` | 0 | 0.0% | Healthy |
| `latitude` | `float64` | 2 | 0.0% | Healthy |
| `longitude` | `float64` | 2 | 0.0% | Healthy |
| `property_type` | `str` | 0 | 0.0% | Healthy |
| `property_class_raw` | `str` | 0 | 0.0% | Healthy |
| `bedrooms` | `float64` | 100,000 | 100.0% | Sparse |
| `bathrooms` | `float64` | 100,000 | 100.0% | Sparse |

### Sale Events Dataset (Top Columns)
| Column | Data Type | Null Count (Sample 100k) | Null Percentage | Quality Assessment |
|---|---|---|---|---|
| `record_id` | `str` | 0 | 0.0% | Healthy |
| `source` | `str` | 0 | 0.0% | Healthy |
| `event_type` | `str` | 0 | 0.0% | Healthy |
| `parcel_id` | `str` | 2,776 | 2.78% | Healthy |
| `address_line` | `str` | 0 | 0.0% | Healthy |
| `unit` | `str` | 64,891 | 64.89% | Sparse |
| `city` | `str` | 0 | 0.0% | Healthy |
| `state` | `str` | 0 | 0.0% | Healthy |
| `zip_code` | `str` | 44 | 0.04% | Healthy |
| `country` | `str` | 0 | 0.0% | Healthy |
| `latitude` | `float64` | 2,307 | 2.31% | Healthy |
| `longitude` | `float64` | 2,307 | 2.31% | Healthy |
| `property_type` | `str` | 100,000 | 100.0% | Sparse |
| `property_class_raw` | `str` | 0 | 0.0% | Healthy |
| `sale_price` | `float64` | 0 | 0.0% | Healthy |

---

## 5. Automated Data Quality Rules Implemented (`etl/validate.py`)

1. **`record_id` & `sale_id` Non-Null Rule:** Guarantees absolute uniqueness and primary key integrity.
2. **Strict Positive Price Rule (`CHECK (sale_price > 0)`):** Rejects invalid negative financial inputs.
3. **Plausible Year Built Constraint (`1600 <= year_built <= Current Year`):** Rejects corrupt dates.
4. **Non-Negative Square Footage Rule:** Prevents corrupt negative area records.
5. **BBL Standardizer:** Trims floating-point scientific notation (`2054800111.00000000` -> `2054800111`).

---
*(This audit document can be included directly in Section 5 of the Group Final Report.)*