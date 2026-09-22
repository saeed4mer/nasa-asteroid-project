-- ==========================================================
-- AWS Athena / Glue Data Catalog DDL
-- NASA Asteroid Intelligence Platform
-- ==========================================================

-- 1. Create Database
CREATE DATABASE IF NOT EXISTS nasa_asteroids;

-- 2. Create External Table for Processed Parquet Data (Primary & Optimized)
CREATE EXTERNAL TABLE IF NOT EXISTS nasa_asteroids.asteroids (
    id STRING,
    name STRING,
    closest_approach_date STRING,
    miss_distance_km DOUBLE,
    hazardous BOOLEAN
)
PARTITIONED BY (
    year STRING,
    month STRING,
    day STRING
)
STORED AS PARQUET
LOCATION 's3://nasa-asteroid-intelligence/processed/'
TBLPROPERTIES (
    'parquet.compression'='SNAPPY',
    'projection.enabled'='true',
    'projection.year.type'='date',
    'projection.year.range'='2020,2030',
    'projection.year.format'='yyyy',
    'projection.month.type'='integer',
    'projection.month.range'='1,12',
    'projection.month.digits'='2',
    'projection.day.type'='integer',
    'projection.day.range'='1,31',
    'projection.day.digits'='2',
    'storage.location.template'='s3://nasa-asteroid-intelligence/processed/year=${year}/month=${month}/day=${day}/'
);

-- 3. Optional: Create External Table for Processed CSV Data
CREATE EXTERNAL TABLE IF NOT EXISTS nasa_asteroids.asteroids_csv (
    id STRING,
    name STRING,
    closest_approach_date STRING,
    miss_distance_km DOUBLE,
    hazardous BOOLEAN
)
PARTITIONED BY (
    year STRING,
    month STRING,
    day STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://nasa-asteroid-intelligence/processed_csv/'
TBLPROPERTIES (
    'skip.header.line.count'='1'
);
