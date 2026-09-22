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


def test_redact_api_key_query_params():
    # Only api_key parameter
    url_single = "http://api.nasa.gov/neo/rest/v1/feed?api_key=SECRET_API_KEY"
    assert (
        nasa_asteroids.redact_api_key(url_single)
        == "http://api.nasa.gov/neo/rest/v1/feed?api_key=REDACTED"
    )

    # api_key between other query parameters
    url_multi = (
        "http://api.nasa.gov/neo/rest/v1/feed"
        "?start_date=2026-09-01&api_key=SECRET_API_KEY&end_date=2026-09-07"
    )
    assert (
        nasa_asteroids.redact_api_key(url_multi)
        == "http://api.nasa.gov/neo/rest/v1/feed?start_date=2026-09-01&api_key=REDACTED&end_date=2026-09-07"
    )

    # api_key at start of query string with subsequent parameter
    url_leading = (
        "http://api.nasa.gov/neo/rest/v1/feed?api_key=SECRET_API_KEY&detailed=false"
    )
    assert (
        nasa_asteroids.redact_api_key(url_leading)
        == "http://api.nasa.gov/neo/rest/v1/feed?api_key=REDACTED&detailed=false"
    )

    # No api_key parameter present
    url_safe = "http://api.nasa.gov/neo/rest/v1/feed?start_date=2026-09-01"
    assert nasa_asteroids.redact_api_key(url_safe) == url_safe

    # Non-string input handled gracefully
    assert nasa_asteroids.redact_api_key(None) is None
    assert nasa_asteroids.redact_api_key(12345) == 12345


def test_sanitize_raw_data_top_level_and_asteroid_links():
    import json

    raw_payload = {
        "links": {
            "next": "http://api.nasa.gov/neo/rest/v1/feed?start_date=2026-09-28&api_key=SECRET_KEY_123",
            "previous": "http://api.nasa.gov/neo/rest/v1/feed?start_date=2026-09-14&api_key=SECRET_KEY_123",
            "self": "http://api.nasa.gov/neo/rest/v1/feed?start_date=2026-09-21&api_key=SECRET_KEY_123"
        },
        "element_count": 1,
        "near_earth_objects": {
            "2026-09-21": [
                {
                    "links": {
                        "self": "http://api.nasa.gov/neo/rest/v1/neo/3183853?api_key=SECRET_KEY_123"
                    },
                    "id": "3183853",
                    "name": "(2004 LA6)",
                    "nasa_jpl_url": "https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=3183853",
                    "is_potentially_hazardous_asteroid": False,
                    "close_approach_data": [
                        {
                            "close_approach_date": "2026-09-22",
                            "miss_distance": {
                                "kilometers": "54500983.17"
                            }
                        }
                    ]
                }
            ]
        }
    }

    sanitized = nasa_asteroids.sanitize_raw_data(raw_payload)

    # Verify secret is completely removed
    sanitized_str = json.dumps(sanitized)
    assert "SECRET_KEY_123" not in sanitized_str

    # Verify links have REDACTED
    assert (
        sanitized["links"]["next"]
        == "http://api.nasa.gov/neo/rest/v1/feed?start_date=2026-09-28&api_key=REDACTED"
    )
    assert (
        sanitized["links"]["previous"]
        == "http://api.nasa.gov/neo/rest/v1/feed?start_date=2026-09-14&api_key=REDACTED"
    )
    assert (
        sanitized["links"]["self"]
        == "http://api.nasa.gov/neo/rest/v1/feed?start_date=2026-09-21&api_key=REDACTED"
    )

    asteroid_link = sanitized["near_earth_objects"]["2026-09-21"][0]["links"]["self"]
    assert (
        asteroid_link
        == "http://api.nasa.gov/neo/rest/v1/neo/3183853?api_key=REDACTED"
    )

    # Verify astronomical / science data is preserved unchanged
    asteroid = sanitized["near_earth_objects"]["2026-09-21"][0]
    assert asteroid["id"] == "3183853"
    assert asteroid["name"] == "(2004 LA6)"
    assert asteroid["nasa_jpl_url"] == "https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=3183853"
    assert asteroid["is_potentially_hazardous_asteroid"] is False
    assert asteroid["close_approach_data"][0]["close_approach_date"] == "2026-09-22"
    assert asteroid["close_approach_data"][0]["miss_distance"]["kilometers"] == "54500983.17"

    # Verify original payload was not mutated
    assert "SECRET_KEY_123" in raw_payload["links"]["self"]


def test_save_raw_json_produces_file_without_secret(tmp_path):
    import json

    test_file = tmp_path / "test_raw.json"
    raw_payload = {
        "links": {
            "self": "http://api.nasa.gov/neo/rest/v1/feed?start_date=2026-09-21&api_key=SUPER_SECRET_KEY"
        },
        "element_count": 1,
        "near_earth_objects": {
            "2026-09-21": [
                {
                    "links": {
                        "self": "http://api.nasa.gov/neo/rest/v1/neo/999?api_key=SUPER_SECRET_KEY"
                    },
                    "id": "999",
                    "name": "Secret Test Asteroid",
                    "is_potentially_hazardous_asteroid": True,
                    "close_approach_data": [
                        {
                            "close_approach_date": "2026-09-21",
                            "miss_distance": {"kilometers": "100000"}
                        }
                    ]
                }
            ]
        }
    }

    nasa_asteroids.save_raw_json(raw_payload, filename=str(test_file))
    assert test_file.exists()

    file_content = test_file.read_text(encoding="utf-8")
    assert "SUPER_SECRET_KEY" not in file_content
    assert "api_key=REDACTED" in file_content

    loaded_json = json.loads(file_content)
    assert loaded_json["element_count"] == 1
    assert loaded_json["near_earth_objects"]["2026-09-21"][0]["name"] == "Secret Test Asteroid"


def test_http_error_redaction():
    import requests

    error_url = (
        "https://api.nasa.gov/neo/rest/v1/feed"
        "?start_date=2026-09-01&api_key=VERY_SECRET_KEY&end_date=2026-09-07"
    )
    http_error = requests.exceptions.HTTPError(
        f"403 Client Error: Forbidden for url: {error_url}"
    )

    redacted_message = nasa_asteroids.redact_api_key(str(http_error))

    assert "VERY_SECRET_KEY" not in redacted_message
    assert "api_key=REDACTED" in redacted_message
    assert "start_date=2026-09-01" in redacted_message
    assert "end_date=2026-09-07" in redacted_message
    assert "403 Client Error: Forbidden for url:" in redacted_message