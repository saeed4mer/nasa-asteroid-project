# NASA Asteroid Intelligence Platform

A data engineering project that ingests Near-Earth Object data from NASA's NeoWs API, validates and transforms the data using Python, and prepares it for downstream SQL analytics, cloud processing, and an interactive intelligence dashboard.

## Problem

Near-Earth Object data contains useful information about asteroid approaches, including approach dates, miss distances, and potentially hazardous classifications. However, raw API responses are deeply nested and are not immediately convenient for analysis.

This project builds a structured data pipeline that takes raw NASA API data, validates it, extracts the relevant fields, and produces a clean dataset that can be used for SQL analytics and downstream data engineering systems.

## Current Pipeline

The current pipeline performs the following steps:

1. **Load configuration**
   - Loads the NASA API key securely from a `.env` file using `python-dotenv`.
   - The API key is excluded from version control through `.gitignore`.

2. **Generate the date window**
   - Dynamically calculates today's date as the start date.
   - Creates a 7-day window using Python's `datetime` and `timedelta`.

3. **Fetch NASA NeoWs data**
   - Sends a request to NASA's Near-Earth Object Web Service (NeoWs) API.
   - Uses the dynamically generated date range and API key.
   - Uses a request timeout and HTTP error handling.

4. **Parse the API response**
   - Converts the JSON response into Python dictionaries.
   - Navigates the nested `near_earth_objects` structure organized by date.

5. **Validate incoming asteroid records**
   - Checks that each asteroid has a name.
   - Checks that close-approach data exists.
   - Checks that miss-distance data exists.
   - Checks that miss distance contains a kilometer value.
   - Invalid records are skipped instead of entering the final dataset.

6. **Transform the data**
   - Extracts only the fields required by the project:
     - Asteroid name
     - Closest approach date
     - Miss distance in kilometers
     - Potentially hazardous classification
   - Converts the nested NASA response into a flat list of dictionaries.

7. **Track data quality**
   - Records how many asteroid records were received.
   - Records how many valid records were produced.
   - Records how many invalid records were skipped.

8. **Write the processed data**
   - Saves the validated asteroid records to `asteroids.csv`.
   - Uses `csv.DictWriter` with a consistent schema.

9. **Logging and error handling**
   - Uses Python's `logging` module to track pipeline execution.
   - Handles HTTP errors, network errors, and unexpected exceptions.

10. **Automated testing**
    - Uses `pytest` to test the extraction and validation logic.
    - Tests valid records, invalid records, missing fields, multiple records, and extracted field values.

### Current Data Flow

```text
NASA NeoWs API
       │
       ▼
Dynamic 7-Day Request
       │
       ▼
Raw JSON Response
       │
       ▼
Parse Nested JSON
       │
       ▼
Validate Records
       │
       ├──────── Invalid → Skip + Count
       │
       ▼
Transform to Structured Records
       │
       ▼
Data Quality Metrics
       │
       ▼
CSV Output
       │
       ▼
Automated Tests
```

## Features

- **Dynamic data ingestion** — Automatically fetches a rolling 7-day window of Near-Earth Object data.
- **Secure API configuration** — Stores the NASA API key in environment variables rather than source code.
- **Data validation** — Rejects incomplete asteroid records before they enter the processed dataset.
- **Data transformation** — Converts NASA's nested JSON response into a structured dataset.
- **Data-quality tracking** — Reports records received, valid records, and skipped records for each run.
- **Error handling** — Handles HTTP, network, and unexpected runtime errors.
- **Structured CSV output** — Produces a consistent, analysis-ready CSV dataset.
- **Logging** — Records important pipeline events and errors.
- **Automated testing** — Uses `pytest` to verify extraction, validation, and transformation logic.
- **Version control** — Project development is tracked using Git and GitHub.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Data ingestion, transformation, validation, and pipeline logic |
| NASA NeoWs API | Source of Near-Earth Object data |
| Requests | HTTP communication with the NASA API |
| python-dotenv | Secure environment-variable management |
| CSV | Current processed-data storage |
| Pytest | Automated testing |
| Git | Version control |
| GitHub | Source-code hosting and project collaboration |

## Data Source

This project uses NASA's **Near Earth Object Web Service (NeoWs)** to retrieve information about Near-Earth Objects.

The pipeline uses the NeoWs feed endpoint to retrieve asteroid data for a dynamically generated 7-day window.

For each asteroid, the current pipeline extracts:

- Asteroid name
- Closest approach date
- Miss distance in kilometers
- Potentially hazardous classification

The raw response is provided as nested JSON and is transformed into a flat, structured dataset before being written to CSV.

## Data Validation

The pipeline validates incoming asteroid records before adding them to the processed dataset.

A record is skipped if:

- The asteroid name is missing.
- Close-approach data is missing.
- Miss-distance data is missing.
- The miss-distance value in kilometers is missing.

The pipeline also tracks data-quality metrics for each run:

- **Records received**
- **Valid records**
- **Skipped records**

This prevents incomplete records from silently entering the downstream dataset and provides visibility into the quality of each ingestion run.

## Testing

The project uses `pytest` to test the core data extraction and validation logic without making live API requests.

The test suite currently covers:

- Valid asteroid records
- Missing asteroid names
- Missing close-approach data
- Missing miss-distance data
- Missing kilometer values
- Correct field extraction
- Processing multiple asteroid records

All current tests pass successfully.

## Project Structure

```text
NASA-Intelligence-Platform/
│
├── nasa_asteroids.py          # Main ingestion and transformation pipeline
├── test_nasa_asteroids.py     # Automated tests
├── asteroids.csv              # Current processed dataset
├── .env                       # Local API credentials (not committed)
├── .gitignore                 # Files excluded from Git
└── README.md                  # Project documentation
```

## How to Run

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd NASA-Intelligence-Platform
```

### 2. Install dependencies

```bash
pip install requests python-dotenv pytest
```

### 3. Configure the NASA API key

Create a `.env` file in the project root:

```text
NASA_API_KEY=your_nasa_api_key
```

The `.env` file is intentionally excluded from Git.

### 4. Run the pipeline

```bash
python nasa_asteroids.py
```

The pipeline will fetch the current 7-day window, validate and transform the data, and generate `asteroids.csv`.

### 5. Run the tests

```bash
python -m pytest
```

All automated tests should pass before changes are committed.

## Current Status

### Completed

- NASA NeoWs API ingestion
- Dynamic 7-day data window
- JSON parsing and transformation
- Data validation
- Data-quality metrics
- CSV generation
- Logging and error handling
- Automated tests
- Environment-variable configuration
- Git/GitHub version control
- Relational database schema design
- SQLite database creation
- CSV-to-SQL data loading
- Python-to-SQLite integration
- SQL aggregation and analytical queries
- Duplicate detection
- SQL data-quality checks
- Asteroid intelligence queries
- Idempotent database loading

### Current Data Architecture

```text
NASA NeoWs API
       |
       v
Python Ingestion
       |
       v
Validation & Transformation
       |
       +------------------+
       |                  |
       v                  v
asteroids.csv       SQLite Database
                         |
                  +------+------+
                  |             |
                  v             v
              asteroids    close_approaches
                  |             |
                  +------+------+
                         |
                         v
                   SQL Analytics
                         |
                         v
                Asteroid Intelligence
```

### Planned

The project will be expanded into a full data engineering platform with:

- SQL-based data storage and analytics
- Improved data modeling
- Incremental and idempotent data loading
- Cloud-based storage and processing on AWS
- Pipeline orchestration and scheduling
- Monitoring and improved observability
- API/data-serving layer
- Interactive asteroid intelligence dashboard
- Automated deployment and CI/CD

## Future Architecture

The current Python → CSV pipeline is the foundation of a larger data engineering platform.

The planned architecture is:

```text
                    NASA NeoWs API
                           │
                           ▼
                  Python Ingestion
                           │
                           ▼
                Validation & Transformation
                           │
                    ┌──────┴──────┐
                    ▼             ▼
               Raw Storage    Processed Data
                                  │
                                  ▼
                           SQL Data Layer
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                    Analytics        Data Quality
                         │
                         ▼
                  API / Data Serving
                         │
                         ▼
                Interactive Dashboard
                         │
                         ▼
                       Users
```

The planned cloud architecture will introduce AWS-based storage, processing, scheduling, monitoring, and deployment as the project progresses.

The final platform is intended to provide an interactive interface for exploring Near-Earth Object activity, including approach dates, miss distances, hazardous classifications, trends, and other derived insights.
