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
    assert asteroid_data[0]["miss_distance_km"] == 123456.78
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


def test_save_to_parquet(tmp_path):
    import pyarrow.parquet as pq

    test_file = tmp_path / "test_asteroids.parquet"
    test_data = [
        {
            "id": "12345",
            "name": "Parquet Test",
            "closest_approach_date": "2026-09-22",
            "miss_distance_km": 150000.5,
            "hazardous": False
        }
    ]
    nasa_asteroids.save_to_parquet(test_data, filename=str(test_file))
    assert test_file.exists()

    table = pq.read_table(str(test_file))
    assert table.num_rows == 1
    assert table.column("name")[0].as_py() == "Parquet Test"
    assert table.column("miss_distance_km")[0].as_py() == 150000.5


def test_fetch_data_mocked():
    from unittest.mock import MagicMock, patch

    mock_payload = {
        "element_count": 1,
        "near_earth_objects": {}
    }
    with patch("nasa_asteroids.get_http_session") as mock_get_session:
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_payload
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session

        data = nasa_asteroids.fetch_data(start="2026-09-01", end="2026-09-07", key="TEST_KEY")
        assert data == mock_payload
        mock_session.get.assert_called_once()


def test_upload_raw_to_s3_mocked():
    from unittest.mock import MagicMock, patch

    with patch("boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        nasa_asteroids.upload_raw_to_s3()

        mock_boto.assert_called_once_with("s3")
        mock_s3.upload_file.assert_called_once()
        call_args = mock_s3.upload_file.call_args[0]
        assert call_args[0] == "asteroids_raw.json"
        assert "raw/year=" in call_args[2]


def test_upload_processed_to_s3_mocked():
    from unittest.mock import MagicMock, patch

    with patch("boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3

        nasa_asteroids.upload_processed_to_s3()

        mock_boto.assert_called_once_with("s3")
        assert mock_s3.upload_file.call_count == 2
        uploaded_files = [call[0][0] for call in mock_s3.upload_file.call_args_list]
        assert "asteroids.parquet" in uploaded_files
        assert "asteroids.csv" in uploaded_files


def test_database_load_data_end_to_end(tmp_path):
    import sqlite3
    import database

    db_file = str(tmp_path / "test_asteroids.db")
    test_records = [
        {
            "id": "999",
            "name": "Integration Asteroid",
            "closest_approach_date": "2026-09-22",
            "miss_distance_km": 500000.0,
            "hazardous": True
        }
    ]

    database.load_data(test_records, db_path=db_file)

    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT asteroid_id, name, hazardous FROM asteroids WHERE asteroid_id = '999'")
        row = cursor.fetchone()
        assert row == ("999", "Integration Asteroid", 1)

        cursor.execute(
            "SELECT asteroid_id, approach_date, miss_distance_km FROM close_approaches WHERE asteroid_id = '999'"
        )
        approach = cursor.fetchone()
        assert approach == ("999", "2026-09-22", 500000.0)