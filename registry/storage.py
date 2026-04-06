from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from registry.config import get_settings


class StorageUnavailableError(Exception):
    pass


class Storage:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.minio_bucket
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_bucket(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as exc:
            raise StorageUnavailableError(str(exc)) from exc

    def upload_bytes(self, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return f"s3://{self.bucket}/{object_name}"
        except Exception as exc:
            raise StorageUnavailableError(str(exc)) from exc

    def presigned_get_url(self, object_name: str, expires_minutes: int = 15) -> str:
        try:
            return self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=object_name,
                expires=timedelta(minutes=expires_minutes),
            )
        except Exception as exc:
            raise StorageUnavailableError(str(exc)) from exc

    def object_exists(self, object_name: str) -> bool:
        try:
            self.client.stat_object(self.bucket, object_name)
            return True
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NoSuchBucket"}:
                return False
            raise StorageUnavailableError(str(exc)) from exc
        except Exception as exc:
            raise StorageUnavailableError(str(exc)) from exc
