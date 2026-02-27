import os
import boto3
from django.conf import settings
from botocore.exceptions import ClientError

class MinioStorageClient:
    """Wrapper around boto3 for MinIO/S3 compatible storage."""

    def __init__(self):
        # Configure MinIO connection from settings or environment variables
        self.endpoint_url = os.environ.get("MINIO_ENDPOINT_URL", "http://localhost:9000")
        self.access_key = os.environ.get("MINIO_ACCESS_KEY", "minio_admin")
        self.secret_key = os.environ.get("MINIO_SECRET_KEY", "minio_secret")
        self.bucket_name = os.environ.get("MINIO_BUCKET_NAME", "dtae-artifacts")
        
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_key_id=self.secret_key,
            config=boto3.session.Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self.ensure_bucket()

    def ensure_bucket(self):
        """Create bucket if it does not exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                except ClientError:
                    # Ignore if another worker is creating it concurrently
                    pass
            else:
                raise

    def upload_file_content(self, key: str, content: str, content_type: str = "text/plain") -> str:
        """Upload string content to a specific key, returning its URL."""
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType=content_type,
        )
        return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{key}"

    def download_file_content(self, key: str) -> str:
        """Download string content from a specific key."""
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read().decode("utf-8")

# Refactor: Optimize imports and clean up code structure.
