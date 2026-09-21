import requests
import csv
import os
import logging
import json 
import boto3

from database import load_data
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
s3 = boto3.client("s3")

# Load variables from .env
load_dotenv(dotenv_path=".env")

API_KEY = os.getenv("NASA_API_KEY")
start_date = date.today()
end_date = start_date + timedelta(days=6)
run_date = date.today().strftime("%d-%m-%Y")
run_time = datetime.now().strftime("%H-%M-%S")

URL = "https://api.nasa.gov/neo/rest/v1/feed"


def fetch_data():
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": API_KEY
    }

    logger.info("Fetching NASA data from %s to %s", start_date, end_date)

    response = requests.get(URL, params=params, timeout=10)
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

def save_raw_json(data):
    with open("asteroids_raw.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

def upload_raw_to_s3():
    s3.upload_file(
        "asteroids_raw.json",
        "nasa-asteroid-intelligence",
        f"raw/{run_date}/{run_time}/asteroids_raw.json"
    )

def upload_processed_to_s3():
    s3.upload_file(
        "asteroids.csv",
        "nasa-asteroid-intelligence",
        f"processed/{run_date}/{run_time}/asteroids.csv"
    )

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


def main():

    if not API_KEY:
        logger.error("NASA_API_KEY was not found.")
        logger.error("Check your .env file.")
        return

    logger.info("Starting NASA asteroid pipeline")

    data = fetch_data()

    logger.info("Saving raw NASA response")
    save_raw_json(data)
    upload_raw_to_s3()

    logger.info("Extracting and validating asteroid data")

    asteroid_data, skipped_records, records_received = extract_asteroids(data)

    logger.info("Saving asteroid data to CSV")

    save_to_csv(asteroid_data)

    logger.info("Uploading processed data to S3")
    upload_processed_to_s3()

    load_data(asteroid_data)
    

    print()
    logger.info("API request successful")
    logger.info("CSV created successfully")
    logger.info("Records received: %d", records_received)
    logger.info("Total valid asteroids: %d", len(asteroid_data))
    logger.info("Skipped invalid records: %d", skipped_records)


try:
    main()

except requests.exceptions.HTTPError as error:
    logger.error("NASA API returned an HTTP error: %s", error)

except requests.exceptions.RequestException as error:
    logger.error("Network error: %s", error)

except Exception as error:
    logger.error("Something went wrong: %s", error)