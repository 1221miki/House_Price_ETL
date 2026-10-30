# Data Directory

This directory stores the US Residential Properties and Sale Events datasets across raw, sample, and processed stages:

## 1. Raw Datasets (`data/raw/`)
Full-scale original source datasets (>350 MB combined, excluded from Git commits via `.gitignore`):
- `properties-00000-of-00001.parquet` (~200 MB, 3,306,420 records) — NYC PLUTO residential property attributes, tax assessments, coordinates, and zoning.
- `sale_events-00000-of-00001.parquet` (~161 MB, 3,703,094 records) — NYC historical sale events, deed transactions, prices, and dates.

## 2. Sample Datasets (`data/samples/`)
Lightweight, referentially-consistent test datasets (<2 MB combined, tracked in Git):
- `properties_sample.parquet` (25,000 records) — Fast offline demos and testing without needing 7M rows in RAM.
- `sale_events_sample.parquet` (5,138 matched records) — Preserves 1:N relational foreign keys against sampled properties.

## 3. Processed Datasets (`data/processed/`)
Destination folder for exported Business Intelligence reports, aggregated summaries, and Tableau/PowerBI CSV exports.
