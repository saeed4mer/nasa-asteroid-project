import requests
import csv
import os
import logging
from datetime import date, timedelta
from dotenv import load_dotenv
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Load variables from .env
load_dotenv(dotenv_path=".env")

API_KEY = os.getenv("NASA_API_KEY")
start_date = date.today()
end_date = start_date + timedelta(days=6)

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

            if not asteroid.get("name"):
                skipped_records +=1
                continue

            if not asteroid.get("close_approach_data"):
                skipped_records +=1
                continue
            
            approach = asteroid["close_approach_data"][0]

            if not approach.get("miss_distance"):
                skipped_records +=1 
                continue
            if not approach["miss_distance"].get("kilometers"):
                skipped_records +=1 
                continue

            asteroid_record = {
                "name": asteroid["name"],
                "closest_approach_date": approach["close_approach_date"],
                "miss_distance_km": approach["miss_distance"]["kilometers"],
                "hazardous": asteroid["is_potentially_hazardous_asteroid"]
            }

            asteroid_data.append(asteroid_record)

    return asteroid_data, skipped_records, records_received


def save_to_csv(asteroid_data):
    with open("asteroids.csv", "w", newline="", encoding="utf-8") as file:

        fieldnames = [
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

    logger.info("Extracting and validating asteroid data")

    asteroid_data, skipped_records, records_received = extract_asteroids(data)

    logger.info("Saving asteroid data to CSV")

    save_to_csv(asteroid_data)

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