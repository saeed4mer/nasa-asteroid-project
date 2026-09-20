# NASA Asteroid Intelligence Platform — Cloud Architecture

## Current Architecture

NASA API
    ↓
Python
    ↓
CSV
    ↓
SQLite
    ↓
SQL Analytics

## Target Cloud Architecture

NASA API
    ↓
Python
    ↓
Amazon S3
    ↓
AWS Glue Data Catalog
    ↓
Amazon Athena
    ↓
SQL Analytics