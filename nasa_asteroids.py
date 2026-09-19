import requests
import csv
import os
from dotenv import load_dotenv


# Load variables from .env
load_dotenv(dotenv_path=".env")

API_KEY = os.getenv("NASA_API_KEY")

URL = "https://api.nasa.gov/neo/rest/v1/feed"


def fetch_data():
    params = {
        "start_date": "2026-09-19",
        "end_date": "2026-09-25",
        "api_key": API_KEY
    }

    response = requests.get(URL, params=params, timeout=10)

    response.raise_for_status()

    return response.json()


def extract_asteroids(data):
    asteroids = data["near_earth_objects"]

    asteroid_data = []

    for date, asteroid_list in asteroids.items():

        for asteroid in asteroid_list:

            approach = asteroid["close_approach_data"][0]

            asteroid_record = {
                "name": asteroid["name"],
                "closest_approach_date": approach["close_approach_date"],
                "miss_distance_km": approach["miss_distance"]["kilometers"],
                "hazardous": asteroid["is_potentially_hazardous_asteroid"]
            }

            asteroid_data.append(asteroid_record)

    return asteroid_data


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
        print("ERROR: NASA_API_KEY was not found.")
        print("Check your .env file.")
        return

    print("Fetching NASA data...")

    data = fetch_data()

    print("Extracting asteroid data...")

    asteroid_data = extract_asteroids(data)

    print("Saving data to CSV...")

    save_to_csv(asteroid_data)

    print()
    print("API request successful!")
    print("CSV created successfully!")
    print("Total asteroids:", len(asteroid_data))


try:
    main()

except requests.exceptions.HTTPError as error:
    print("NASA API returned an HTTP error:")
    print(error)

except requests.exceptions.RequestException as error:
    print("Network error:")
    print(error)

except Exception as error:
    print("Something went wrong:")
    print(error)