# NASA Asteroid Intelligence Platform

A data engineering project that ingests Near-Earth Object (NEO) data from NASA's NeoWs API, validates and transforms it with Python, stores it locally and in Amazon S3, prepares analytics-ready Parquet data for Amazon Athena, and presents asteroid intelligence through an interactive Streamlit dashboard.

![Tests](https://img.shields.io/badge/tests-12%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.x-blue)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-informational)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Pipeline Workflow](#pipeline-workflow)
- [Data Quality](#data-quality)
- [SQL Analytics](#sql-analytics)
- [Testing](#testing)
- [Continuous Integration](#continuous-integration)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Running the Project](#running-the-project)
- [Current Status](#current-status)
- [Future Engineering Improvements](#future-engineering-improvements)
- [Project Goal](#project-goal)

---

## Project Overview

NASA's Near-Earth Object Web Service (NeoWs) provides valuable information about asteroid approaches, including:

- Asteroid identity
- Closest approach dates
- Miss distances
- Potentially hazardous classifications

The raw API response is deeply nested and not immediately suitable for analytics.

This project builds an **end-to-end data engineering pipeline** that transforms that raw API data into structured, validated, analytics-ready datasets and exposes the resulting information through SQL analytics and an interactive intelligence dashboard.

---

## Architecture

### Local Development Pipeline

```
NASA NeoWs API
      ↓
Python Ingestion
      ↓
Validation & Transformation
      ↓
CSV + SQLite
      ↓
SQL Analytics
```

### Cloud Analytics Pipeline

```
NASA NeoWs API
      ↓
Python ETL Pipeline
      ↓
Amazon S3
   ┌──────┴──────┐
   ↓             ↓
Raw JSON   Processed Parquet
                  ↓
            Amazon Athena
                  ↓
            SQL Analytics
                  ↓
       Intelligence Dashboard
```

The project uses **S3** as the cloud storage layer and **Athena** as the serverless analytical query layer.

---

## Pipeline Workflow

### 1. Configuration

- Configuration is loaded from environment variables using `python-dotenv`.
- Sensitive credentials are stored locally in `.env` and excluded from version control.
- A `.env.example` file is provided as a configuration template.

### 2. NASA API Ingestion

The pipeline retrieves Near-Earth Object data from NASA's NeoWs feed API.

- The default ingestion window is dynamically generated from the current date.
- Custom date ranges are supported via CLI arguments:

```bash
python nasa_asteroids.py --start-date 2026-09-01 --end-date 2026-09-07
```

### 3. API Reliability

The HTTP client includes:

- Request timeouts
- Retry handling with exponential backoff
- HTTP error handling
- Network error handling

Retry handling covers common transient HTTP responses: `429`, `500`, `502`, `503`, `504`.

### 4. Data Extraction

NASA's nested JSON response is parsed to extract the fields required for downstream processing:

| Field | Description |
|---|---|
| `id` | NASA asteroid identifier |
| `name` | Asteroid name |
| `closest_approach_date` | Closest approach date |
| `miss_distance_km` | Miss distance in kilometers |
| `hazardous` | Potentially hazardous classification |

### 5. Data Validation

Incoming records are validated before entering the processed dataset. Records are skipped when required information is missing or invalid, including:

- Asteroid ID
- Asteroid name
- Close-approach data
- Close-approach date
- Miss-distance information (raw and km value)
- Valid hazardous classification

The pipeline tracks **records received**, **valid records**, and **skipped records** for every run.

### 6. Local Data Storage

Validated data is written to:

- `asteroids.csv`
- `asteroids.parquet` (explicit PyArrow schema, Snappy compression)

Processed records are also loaded into **SQLite** for relational analytics.

### 7. Relational Database

The local SQLite database contains two related tables:

```
asteroids
    │
    │ 1-to-many
    ↓
close_approaches
```

The database loader is **idempotent**, preventing duplicate asteroid and close-approach records from being inserted on repeated pipeline runs.

### 8. Amazon S3

The pipeline uploads data to S3 using run-based, date-partitioned paths.

Processed Parquet data:

```
processed/
└── year=YYYY/
    └── month=MM/
        └── day=DD/
            └── asteroids_<run-time>.parquet
```

Processed CSV data:

```
processed_csv/
└── year=YYYY/
    └── month=MM/
        └── day=DD/
            └── asteroids_<run-time>.csv
```

Raw API responses are kept outside version control.

### 9. Amazon Athena

Processed Parquet data is designed for analytical querying through Amazon Athena. Prepared SQL analytics include:

- Total asteroid count
- Potentially hazardous asteroid count
- Closest / farthest approaches
- Average miss distance
- Hazardous vs. non-hazardous distribution
- Close approaches by date
- Potentially hazardous objects beyond a specified distance

### 10. Intelligence Dashboard

An interactive **Streamlit** dashboard provides:

- Interactive asteroid visualization
- Hazardous / nominal filtering
- Miss-distance filtering
- Asteroid selection with identifiers, closest approach dates, miss distances, and lunar-distance equivalents
- Hazard classification display

> Note: the orbital visualization is an illustrative visual model, not an astronomical ephemeris calculation.

---

## Data Quality

The pipeline explicitly tracks ingestion quality on every run:

- Records received
- Valid records
- Skipped records

Validation occurs **before** data enters the processed datasets or relational database, preventing incomplete records from silently propagating downstream.

---

## SQL Analytics

A dedicated Athena query collection lives in [`athena_queries.sql`](athena_queries.sql), including:

- Total asteroid count
- Potentially hazardous asteroid count
- Closest asteroid approaches
- Average miss distance
- Hazardous vs. non-hazardous distribution
- Closest potentially hazardous objects

The local SQLite layer provides an additional relational analytics environment for development and validation.

---

## Testing

The project uses `pytest`. The current suite contains **12 tests**, covering:

- Valid asteroid extraction
- Missing asteroid names
- Missing close-approach data
- Missing miss-distance data
- Missing kilometer values
- Extracted field correctness
- Multiple asteroid records
- Parquet generation
- Mocked NASA API requests
- Mocked S3 uploads
- Database integration
- Database loading behavior

**Current status:** ✅ 12 passed

Tests are designed to avoid making live NASA API requests.

---

## Continuous Integration

The repository includes a GitHub Actions workflow at `.github/workflows/ci.yml` that:

1. Checks out the repository
2. Sets up Python
3. Installs project dependencies
4. Runs the pytest suite

---

## Project Structure

```
NASA-Intelligence-Platform/
│
├── nasa_asteroids.py
├── database.py
├── dashboard.py
│
├── test_nasa_asteroids.py
│
├── schema.sql
├── athena_schema.sql
├── athena_queries.sql
│
├── asteroids.csv
├── asteroids.parquet
│
├── architecture.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
└── README.md
```

Local-only files such as `.env`, SQLite databases, and raw API responses are excluded from version control.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Ingestion, transformation, validation, pipeline orchestration |
| NASA NeoWs API | Source data |
| Requests | API communication |
| python-dotenv | Environment configuration |
| Pandas | Data handling for the dashboard |
| PyArrow | Parquet generation and schema management |
| SQLite | Local relational data storage |
| SQL | Data analytics |
| Amazon S3 | Cloud object storage |
| Amazon Athena | Serverless SQL analytics |
| Boto3 | AWS integration |
| Streamlit | Interactive intelligence dashboard |
| Pytest | Automated testing |
| Git | Version control |
| GitHub Actions | Continuous integration |

---

## Running the Project

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd NASA-Intelligence-Platform
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file:

```env
NASA_API_KEY=your_nasa_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=nasa-asteroid-intelligence
```

> ⚠️ Never commit `.env` to version control.

### 4. Run the ingestion pipeline

```bash
python nasa_asteroids.py
```

Or specify a custom date range:

```bash
python nasa_asteroids.py --start-date 2026-09-01 --end-date 2026-09-07
```

### 5. Run tests

```bash
pytest -v
```

### 6. Launch the dashboard

```bash
streamlit run dashboard.py
```

---

## Current Status

### ✅ Implemented

- NASA NeoWs API ingestion
- Dynamic date-window ingestion
- Custom CLI date ranges
- API timeout, retry, and backoff handling
- JSON parsing
- Data validation and data-quality metrics
- CSV and Parquet generation
- SQLite relational database with idempotent loading
- Local SQL analytics
- Amazon S3 integration with raw/processed separation and partitioned layout
- Amazon Athena schema and analytical queries
- Interactive Streamlit dashboard
- Automated testing (pytest)
- GitHub Actions CI
- Environment-based configuration
- Architecture documentation

### 🚧 In Progress

- End-to-end cloud analytics validation
- Further data-quality validation
- Production-level orchestration and scheduling
- Expanded intelligence metrics
- Historical asteroid analysis
- Final portfolio documentation

---

## Future Engineering Improvements

- Pipeline orchestration and scheduling
- Automated data-quality monitoring
- Historical data accumulation, incremental processing, and backfills
- Schema evolution handling
- Improved observability
- Pipeline failure recovery
- Advanced asteroid risk and priority metrics
- Historical trend analysis
- API/data-serving layer
- Dashboard expansion
- Deployment automation

---

## Project Goal

The goal of this project is to demonstrate an end-to-end data engineering workflow using a real-world scientific data source:

```
Data Ingestion → Data Validation → Data Transformation → Data Storage
    → Cloud Data Lake → SQL Analytics → Data Intelligence → Interactive Visualization
```

The resulting system provides a foundation for exploring Near-Earth Object activity and building analytical intelligence around asteroid approaches, miss distances, hazardous classifications, and historical patterns.
