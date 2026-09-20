import nasa_asteroids
def test_extract_asteroids():
    fake_data = {
        "near_earth_objects": {
            "2026-09-20": [
                {   
                    "id": "123456",
                    "name": "Test Asteroid",
                    "is_potentially_hazardous_asteroid": False,
                    "close_approach_data": [
                        {
                            "close_approach_date": "2026-09-20",
                            "miss_distance": {
                                "kilometers": "123456.78"
                            }
                        }
                    ]
                }
            ]
        }
    }

    asteroid_data, skipped_records, records_received = (
        nasa_asteroids.extract_asteroids(fake_data)
    )

    assert len(asteroid_data) == 1
    assert skipped_records == 0
    assert records_received == 1

def test_skip_asteroid_without_name():
    fake_data = {
        "near_earth_objects": {
            "2026-09-20": [
                {    
                    "id": "123456",
                    "name": "",
                    "is_potentially_hazardous_asteroid": False,
                    "close_approach_data": [
                        {
                            "close_approach_date": "2026-09-20",
                            "miss_distance": {
                                "kilometers": "123456.78"
                            }
                        }
                    ]
                }
            ]
        }
    }

    asteroid_data, skipped_records, records_received = (
        nasa_asteroids.extract_asteroids(fake_data)
    )

    assert len(asteroid_data) == 0
    assert skipped_records == 1
    assert records_received == 1

def test_skip_asteroid_without_close_approach_data():
    fake_data = {
        "near_earth_objects": {
            "2026-09-20": [
                {   
                    "id": "123456",
                    "name": "Test Asteroid",
                    "is_potentially_hazardous_asteroid": False,
                    "close_approach_data": []
                }
            ]
        }
    }

    asteroid_data, skipped_records, records_received = (
        nasa_asteroids.extract_asteroids(fake_data)
    )

    assert len(asteroid_data) == 0
    assert skipped_records == 1
    assert records_received == 1

def test_skip_asteroid_without_miss_distance():
    fake_data = {
        "near_earth_objects": {
            "2026-09-20": [
                {    
                    "id": "123456",
                    "name": "Test Asteroid",
                    "is_potentially_hazardous_asteroid": False,
                    "close_approach_data": [
                        {
                            "close_approach_date": "2026-09-20",
                            "miss_distance": {}
                        }
                    ]
                }
            ]
        }
    }

    asteroid_data, skipped_records, records_received = (
        nasa_asteroids.extract_asteroids(fake_data)
    )

    assert len(asteroid_data) == 0
    assert skipped_records == 1
    assert records_received == 1

def test_skip_asteroid_without_kilometers():
    fake_data = {
        "near_earth_objects": {
            "2026-09-20": [
                {    
                    "id": "123456",
                    "name": "Test Asteroid",
                    "is_potentially_hazardous_asteroid": False,
                    "close_approach_data": [
                        {
                            "close_approach_date": "2026-09-20",
                            "miss_distance": {
                                "kilometers": ""
                            }
                        }
                    ]
                }
            ]
        }
    }

    asteroid_data, skipped_records, records_received = (
        nasa_asteroids.extract_asteroids(fake_data)
    )

    assert len(asteroid_data) == 0
    assert skipped_records == 1
    assert records_received == 1

def test_extracted_asteroid_fields():
    fake_data = {
        "near_earth_objects": {
            "2026-09-20": [
                {    
                    "id": "123456",
                    "name": "Test Asteroid",
                    "is_potentially_hazardous_asteroid": True,
                    "close_approach_data": [
                        {
                            "close_approach_date": "2026-09-20",
                            "miss_distance": {
                                "kilometers": "123456.78"
                            }
                        }
                    ]
                }
            ]
        }
    }

    asteroid_data, skipped_records, records_received = (
        nasa_asteroids.extract_asteroids(fake_data)
    )

    assert asteroid_data[0]["name"] == "Test Asteroid"
    assert asteroid_data[0]["closest_approach_date"] == "2026-09-20"
    assert asteroid_data[0]["miss_distance_km"] == "123456.78"
    assert asteroid_data[0]["hazardous"] is True

def test_extract_multiple_asteroids():
    fake_data = {
        "near_earth_objects": {
            "2026-09-20": [
                {
                    "id": "123456",
                    "name": "Asteroid One",
                    "is_potentially_hazardous_asteroid": False,
                    "close_approach_data": [
                        {
                            "close_approach_date": "2026-09-20",
                            "miss_distance": {
                                "kilometers": "100000"
                            }
                        }
                    ]
                },
                {
                    "id": "123456",
                    "name": "Asteroid Two",
                    "is_potentially_hazardous_asteroid": True,
                    "close_approach_data": [
                        {
                            "close_approach_date": "2026-09-20",
                            "miss_distance": {
                                "kilometers": "200000"
                            }
                        }
                    ]
                }
            ]
        }
    }

    asteroid_data, skipped_records, records_received = (
        nasa_asteroids.extract_asteroids(fake_data)
    )

    assert len(asteroid_data) == 2
    assert skipped_records == 0
    assert records_received == 2