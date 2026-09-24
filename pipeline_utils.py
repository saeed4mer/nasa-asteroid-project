"""Shared ingestion foundation utilities for the NASA Intelligence Platform.

Provides reusable, source-agnostic primitives for:
- HTTP requests with exponential backoff and retry
- API key redaction in URLs, text, and error messages
- S3 file uploads with user metadata and error handling
- PyArrow Parquet serialization
- Standardized lineage metadata dictionary generation
"""
import logging
import re

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import pyarrow as pa
import pyarrow.parquet as pq
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)


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


def redact_api_key(text):
    """Safely redact api_key query parameters from a URL or text string."""
    if not isinstance(text, str):
        return text
    return re.sub(r'([?&]api_key=)[^&"\'\s]+', r'\g<1>REDACTED', text)


def upload_file_to_s3(local_file_path, bucket_name, s3_key, metadata=None, s3_client=None):
    """Generic S3 file upload primitive.

    Uploads a local file to S3 with optional metadata and error handling.
    The caller supplies the complete S3 key and bucket name.
    """
    extra_kwargs = {"ExtraArgs": {"Metadata": metadata}} if metadata else {}
    run_id = metadata.get("run_id") if isinstance(metadata, dict) else None
    prefix = f"[{run_id}] " if run_id else ""

    s3 = s3_client or boto3.client("s3")
    try:
        s3.upload_file(
            local_file_path,
            bucket_name,
            s3_key,
            **extra_kwargs
        )
        logger.info("%sUploaded %s to s3://%s/%s", prefix, local_file_path, bucket_name, s3_key)
    except (BotoCoreError, ClientError) as error:
        logger.error(
            "%sS3 upload failed for %s to s3://%s/%s: %s",
            prefix,
            local_file_path,
            bucket_name,
            s3_key,
            redact_api_key(str(error))
        )
        raise


def write_parquet(records, schema, output_path, compression="snappy"):
    """Generic PyArrow Parquet writer.

    Accepts an explicit PyArrow schema and list of record dicts.
    """
    table = pa.Table.from_pylist(records, schema=schema)
    pq.write_table(table, output_path, compression=compression)


def build_lineage_metadata(source_name, run_id, ingested_at):
    """Construct standard lineage metadata dictionary."""
    return {
        "run_id": run_id,
        "ingested_at": ingested_at,
        "source": source_name
    }
