"""Tests for shared ingestion foundation utilities in pipeline_utils.py."""
import logging
from unittest.mock import MagicMock, patch

from botocore.exceptions import BotoCoreError, ClientError
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import pipeline_utils


def test_get_http_session_default_configuration():
    session = pipeline_utils.get_http_session()
    adapter_https = session.adapters.get("https://")
    adapter_http = session.adapters.get("http://")

    assert adapter_https is not None
    assert adapter_http is not None

    retries = adapter_https.max_retries
    assert retries.total == 3
    assert retries.backoff_factor == 1
    assert set(retries.status_forcelist) == {429, 500, 502, 503, 504}
    assert retries.allowed_methods == ["GET"]


def test_get_http_session_custom_configuration():
    session = pipeline_utils.get_http_session(total_retries=5, backoff_factor=2)
    adapter = session.adapters.get("https://")
    assert adapter.max_retries.total == 5
    assert adapter.max_retries.backoff_factor == 2


def test_redact_api_key():
    url_single = "http://api.nasa.gov/test?api_key=SECRET_TOKEN"
    assert (
        pipeline_utils.redact_api_key(url_single)
        == "http://api.nasa.gov/test?api_key=REDACTED"
    )

    url_multi = "http://api.nasa.gov/test?param1=val&api_key=SECRET_TOKEN&param2=123"
    assert (
        pipeline_utils.redact_api_key(url_multi)
        == "http://api.nasa.gov/test?param1=val&api_key=REDACTED&param2=123"
    )

    url_clean = "http://api.nasa.gov/test?param1=val"
    assert pipeline_utils.redact_api_key(url_clean) == url_clean

    assert pipeline_utils.redact_api_key(None) is None
    assert pipeline_utils.redact_api_key(42) == 42


def test_build_lineage_metadata():
    metadata = pipeline_utils.build_lineage_metadata(
        source_name="test_source",
        run_id="abc123def456",
        ingested_at="2026-09-25T01:00:00+00:00"
    )
    assert metadata == {
        "run_id": "abc123def456",
        "ingested_at": "2026-09-25T01:00:00+00:00",
        "source": "test_source"
    }


def test_upload_file_to_s3_success():
    mock_s3 = MagicMock()
    metadata = {"run_id": "run-001"}

    with patch("boto3.client", return_value=mock_s3) as mock_boto:
        pipeline_utils.upload_file_to_s3(
            local_file_path="sample.json",
            bucket_name="test-bucket",
            s3_key="raw/sample.json",
            metadata=metadata
        )

        mock_boto.assert_called_once_with("s3")
        mock_s3.upload_file.assert_called_once_with(
            "sample.json",
            "test-bucket",
            "raw/sample.json",
            ExtraArgs={"Metadata": metadata}
        )


def test_upload_file_to_s3_with_existing_client():
    mock_s3 = MagicMock()
    pipeline_utils.upload_file_to_s3(
        local_file_path="sample.parquet",
        bucket_name="test-bucket",
        s3_key="processed/sample.parquet",
        s3_client=mock_s3
    )

    mock_s3.upload_file.assert_called_once_with(
        "sample.parquet",
        "test-bucket",
        "processed/sample.parquet"
    )


def test_upload_file_to_s3_handles_client_error(caplog):
    mock_s3 = MagicMock()
    client_error = ClientError({"Error": {"Code": "403", "Message": "Forbidden"}}, "PutObject")
    mock_s3.upload_file.side_effect = client_error

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ClientError) as exc_info:
            pipeline_utils.upload_file_to_s3(
                local_file_path="sample.json",
                bucket_name="test-bucket",
                s3_key="raw/sample.json",
                s3_client=mock_s3
            )

    assert exc_info.value == client_error
    assert "S3 upload failed for sample.json" in caplog.text


def test_upload_file_to_s3_handles_botocore_error(caplog):
    mock_s3 = MagicMock()
    boto_error = BotoCoreError()
    mock_s3.upload_file.side_effect = boto_error

    with caplog.at_level(logging.ERROR):
        with pytest.raises(BotoCoreError) as exc_info:
            pipeline_utils.upload_file_to_s3(
                local_file_path="sample.json",
                bucket_name="test-bucket",
                s3_key="raw/sample.json",
                s3_client=mock_s3
            )

    assert exc_info.value == boto_error
    assert "S3 upload failed for sample.json" in caplog.text


def test_upload_file_to_s3_redacts_api_key_in_error_log(caplog):
    mock_s3 = MagicMock()
    client_error = ClientError(
        {"Error": {"Code": "403", "Message": "AccessDenied url https://s3.amazonaws.com?api_key=SECRET_AWS_KEY"}},
        "PutObject"
    )
    mock_s3.upload_file.side_effect = client_error

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ClientError):
            pipeline_utils.upload_file_to_s3(
                local_file_path="sample.json",
                bucket_name="test-bucket",
                s3_key="raw/sample.json",
                s3_client=mock_s3
            )

    assert "SECRET_AWS_KEY" not in caplog.text
    assert "api_key=REDACTED" in caplog.text


def test_write_parquet_success(tmp_path):
    output_path = tmp_path / "test.parquet"
    test_schema = pa.schema([
        ("id", pa.string()),
        ("value", pa.float64())
    ])
    records = [
        {"id": "rec1", "value": 12.34},
        {"id": "rec2", "value": 56.78}
    ]

    pipeline_utils.write_parquet(records, schema=test_schema, output_path=str(output_path))

    assert output_path.exists()
    table = pq.read_table(str(output_path))
    assert table.num_rows == 2
    assert table.column("id").to_pylist() == ["rec1", "rec2"]
    assert table.column("value").to_pylist() == [12.34, 56.78]
