import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

os.environ["SKIP_STORAGE_INIT"] = "true"

from registry.api.versions_router import get_storage
from registry.app import app
from registry.database import Base, get_db


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def upload_bytes(self, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self.objects[object_name] = data
        return f"s3://models/{object_name}"

    def object_exists(self, object_name: str) -> bool:
        return object_name in self.objects

    def presigned_get_url(self, object_name: str, expires_minutes: int = 15) -> str:
        return f"http://fake-minio/{object_name}"

    def ensure_bucket(self) -> None:
        return None


@pytest.fixture
def client() -> TestClient:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    Base.metadata.create_all(bind=engine)
    storage = FakeStorage()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = lambda: storage

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
