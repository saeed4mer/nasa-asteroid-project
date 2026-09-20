import sqlite3


def load_data(asteroid_data):
    conn = sqlite3.connect("asteroids.db")
    cursor = conn.cursor()

    for row in asteroid_data:

        cursor.execute(
            """
            INSERT OR IGNORE INTO asteroids (
                asteroid_id,
                name,
                hazardous
            )
            VALUES (?, ?, ?)
            """,
            (
                row["id"],
                row["name"],
                row["hazardous"]
            )
        )

        cursor.execute(
            """
            INSERT INTO close_approaches (
                asteroid_id,
                approach_date,
                miss_distance_km
            )
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM close_approaches
                WHERE asteroid_id = ?
                  AND approach_date = ?
            )
            """,
            (
                row["id"],
                row["closest_approach_date"],
                row["miss_distance_km"],
                row["id"],
                row["closest_approach_date"]
            )
        )

    conn.commit()
    conn.close()