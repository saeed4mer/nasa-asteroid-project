import argparse
import copy
import csv
import json 
import logging
import os
import re
import sys
from datetime import date, datetime, timedelta

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from database import load_data
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Load variables from .env
load_dotenv(dotenv_path=".env")

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "nasa-asteroid-intelligence")
API_KEY = os.getenv("NASA_API_KEY")
start_date = date.today()
end_date = start_date + timedelta(days=6)
run_year = date.today().strftime("%Y")
run_month = date.today().strftime("%m")
run_day = date.today().strftime("%d")
run_time = datetime.now().strftime("%H-%M-%S")

ASTEROID_SCHEMA = pa.schema([
    ("id", pa.string()),
    ("name", pa.string()),
    ("closest_approach_date", pa.string()),
    ("miss_distance_km", pa.float64()),
    ("hazardous", pa.bool_())
])

URL = "https://api.nasa.gov/neo/rest/v1/feed"


def get_http_session(total_retries=3, backoff_factor=1):
    """Create a requests session configured with retries and exponential backoff."""
    session = requests.Session()
    retries = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_data(start=None, end=None, key=None):
    start = start or start_date
    end = end or end_date
    key = key or API_KEY

    start_str = start.strftime("%Y-%m-%d") if isinstance(start, (date, datetime)) else str(start)
    end_str = end.strftime("%Y-%m-%d") if isinstance(end, (date, datetime)) else str(end)

    params = {
        "start_date": start_str,
        "end_date": end_str,
        "api_key": key
    }

    logger.info("Fetching NASA data from %s to %s", start_str, end_str)

    session = get_http_session()
    response = session.get(URL, params=params, timeout=15)
    response.raise_for_status()

    return response.json()


def extract_asteroids(data):
    asteroids = data["near_earth_objects"]
    asteroid_data = []
    skipped_records = 0
    records_received = 0

    for date, asteroid_list in asteroids.items():
        for asteroid in asteroid_list:
            records_received +=1

            if not asteroid.get("id"):
                skipped_records += 1
                continue

            if not asteroid.get("name"):
                skipped_records +=1
                continue

            if not asteroid.get("close_approach_data"):
                skipped_records +=1
                continue
            
            approach = asteroid["close_approach_data"][0]

            if not approach.get("close_approach_date"):
                skipped_records += 1
                continue


            if not approach.get("miss_distance"):
                skipped_records +=1 
                continue
            miss_distance = approach["miss_distance"].get("kilometers")

            if not miss_distance:
                skipped_records += 1
                continue

            try:
                miss_distance = float(miss_distance)
            except (TypeError, ValueError):
                skipped_records += 1
                continue

            if miss_distance <= 0:
                skipped_records += 1
                continue

            hazardous = asteroid.get("is_potentially_hazardous_asteroid")

            if not isinstance(hazardous, bool):
                skipped_records += 1
                continue

            asteroid_record = {
                "id": asteroid["id"],
                "name": asteroid["name"],
                "closest_approach_date": approach["close_approach_date"],
                "miss_distance_km": miss_distance,
                "hazardous": hazardous
            }

            asteroid_data.append(asteroid_record)

            


    return asteroid_data, skipped_records, records_received

def redact_api_key(text):
    """Safely redact api_key query parameters from a URL or text string."""
    if not isinstance(text, str):
        return text
    return re.sub(r'([?&]api_key=)[^&"\'\s]+', r'\g<1>REDACTED', text)


def sanitize_raw_data(data):
    """Sanitize API-key-bearing URL values in top-level and per-asteroid links."""
    if not isinstance(data, dict):
        return data

    sanitized = copy.deepcopy(data)

    if "links" in sanitized and isinstance(sanitized["links"], dict):
        for key, val in sanitized["links"].items():
            if isinstance(val, str):
                sanitized["links"][key] = redact_api_key(val)

    if "near_earth_objects" in sanitized and isinstance(sanitized["near_earth_objects"], dict):
        for asteroid_list in sanitized["near_earth_objects"].values():
            if isinstance(asteroid_list, list):
                for asteroid in asteroid_list:
                    if isinstance(asteroid, dict) and "links" in asteroid and isinstance(asteroid["links"], dict):
                        for key, val in asteroid["links"].items():
                            if isinstance(val, str):
                                asteroid["links"][key] = redact_api_key(val)

    return sanitized


def save_raw_json(data, filename="asteroids_raw.json"):
    sanitized = sanitize_raw_data(data)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(sanitized, file, indent=4)

def upload_raw_to_s3():
    s3 = boto3.client("s3")
    s3_key = f"raw/year={run_year}/month={run_month}/day={run_day}/asteroids_raw_{run_time}.json"
    try:
        s3.upload_file(
            "asteroids_raw.json",
            S3_BUCKET_NAME,
            s3_key
        )
        logger.info("Uploaded raw JSON to s3://%s/%s", S3_BUCKET_NAME, s3_key)
    except (BotoCoreError, ClientError) as error:
        logger.error(
            "Raw S3 upload failed for s3://%s/%s: %s",
            S3_BUCKET_NAME,
            s3_key,
            redact_api_key(str(error))
        )
        raise

def upload_processed_to_s3():
    s3 = boto3.client("s3")
    parquet_key = f"processed/year={run_year}/month={run_month}/day={run_day}/asteroids_{run_time}.parquet"
    try:
        s3.upload_file(
            "asteroids.parquet",
            S3_BUCKET_NAME,
            parquet_key
        )
        logger.info("Uploaded processed Parquet to s3://%s/%s", S3_BUCKET_NAME, parquet_key)
    except (BotoCoreError, ClientError) as error:
        logger.error(
            "Processed Parquet S3 upload failed for s3://%s/%s: %s",
            S3_BUCKET_NAME,
            parquet_key,
            redact_api_key(str(error))
        )
        raise

    csv_key = f"processed_csv/year={run_year}/month={run_month}/day={run_day}/asteroids_{run_time}.csv"
    try:
        s3.upload_file(
            "asteroids.csv",
            S3_BUCKET_NAME,
            csv_key
        )
        logger.info("Uploaded processed CSV to s3://%s/%s", S3_BUCKET_NAME, csv_key)
    except (BotoCoreError, ClientError) as error:
        logger.error(
            "Processed CSV S3 upload failed for s3://%s/%s (Parquet upload already succeeded at s3://%s/%s): %s",
            S3_BUCKET_NAME,
            csv_key,
            S3_BUCKET_NAME,
            parquet_key,
            redact_api_key(str(error))
        )
        raise

def save_to_parquet(asteroid_data, filename="asteroids.parquet"):
    table = pa.Table.from_pylist(asteroid_data, schema=ASTEROID_SCHEMA)
    pq.write_table(table, filename, compression="snappy")

def save_to_csv(asteroid_data):
    with open("asteroids.csv", "w", newline="", encoding="utf-8") as file:

        fieldnames = [
    "id",
    "name",
    "closest_approach_date",
    "miss_distance_km",
    "hazardous"
]           

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(asteroid_data)


def parse_args():
    parser = argparse.ArgumentParser(
        description="NASA Asteroid Intelligence Platform — Ingestion & ETL Pipeline"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for NASA feed (YYYY-MM-DD). Default: today",
        default=None
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for NASA feed (YYYY-MM-DD). Default: start_date + 6 days",
        default=None
    )
    return parser.parse_args()


def main(start_date_str=None, end_date_str=None):

    if not API_KEY:
        logger.error("NASA_API_KEY was not found.")
        logger.error("Check your .env file.")
        return 1

    if start_date_str:
        try:
            resolved_start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            logger.error("Invalid --start-date format: %s. Expected YYYY-MM-DD.", start_date_str)
            return 1
    else:
        resolved_start = date.today()

    if end_date_str:
        try:
            resolved_end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            logger.error("Invalid --end-date format: %s. Expected YYYY-MM-DD.", end_date_str)
            return 1
    else:
        resolved_end = resolved_start + timedelta(days=6)

    if resolved_end < resolved_start:
        logger.error("End date (%s) cannot be before start date (%s).", resolved_end, resolved_start)
        return 1

    days_diff = (resolved_end - resolved_start).days
    if days_diff > 7:
        logger.warning(
            "NASA NeoWs API limits queries to 7 days per request (requested: %d days). "
            "NASA may reject or truncate the response.",
            days_diff
        )

    logger.info("Starting NASA asteroid pipeline")

    data = fetch_data(start=resolved_start, end=resolved_end, key=API_KEY)

    logger.info("Saving raw NASA response")
    save_raw_json(data)

    logger.info("Extracting and validating asteroid data")

    asteroid_data, skipped_records, records_received = extract_asteroids(data)

    logger.info("Saving asteroid data to CSV and Parquet")

    save_to_csv(asteroid_data)
    save_to_parquet(asteroid_data)

    load_data(asteroid_data)

    logger.info("Uploading raw NASA response to S3")
    upload_raw_to_s3()

    logger.info("Uploading processed data to S3")
    upload_processed_to_s3()
    

    print()
    logger.info("API request successful")
    logger.info("CSV and Parquet created successfully")
    logger.info("Records received: %d", records_received)
    logger.info("Total valid asteroids: %d", len(asteroid_data))
    logger.info("Skipped invalid records: %d", skipped_records)
    return 0


if __name__ == "__main__":
    args = parse_args()
    try:
        exit_code = main(
            start_date_str=args.start_date,
            end_date_str=args.end_date
        )
        sys.exit(exit_code or 0)

    except requests.exceptions.HTTPError as error:
        logger.error(
            "NASA API returned an HTTP error: %s",
            redact_api_key(str(error))
        )
        sys.exit(1)

    except requests.exceptions.RequestException as error:
        logger.error(
            "Network error: %s",
            redact_api_key(str(error))
        )
        sys.exit(1)

    except Exception as error:
        logger.error(
            "Pipeline failure: %s",
            redact_api_key(str(error))
        )
        sys.exit(1)