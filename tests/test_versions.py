from registry.config import get_settings


def test_versions_and_stage_flow(client):
    client.post("/api/v1/models", json={"name": "ranker"})

    v1_resp = client.post(
        "/api/v1/models/ranker/versions",
        json={"metrics": {"ndcg": 0.71}, "parameters": {"lr": 0.01}, "tags": {"dataset": "A"}},
    )
    assert v1_resp.status_code == 201
    assert v1_resp.json()["version"] == 1

    v2_resp = client.post(
        "/api/v1/models/ranker/versions",
        json={"metrics": {"ndcg": 0.75}, "stage": "staging"},
    )
    assert v2_resp.status_code == 201
    assert v2_resp.json()["version"] == 2
    assert v2_resp.json()["stage"] == "staging"

    promote_v1 = client.put("/api/v1/models/ranker/versions/1/stage", json={"stage": "production"})
    assert promote_v1.status_code == 200
    assert promote_v1.json()["stage"] == "production"

    promote_v2 = client.put("/api/v1/models/ranker/versions/2/stage", json={"stage": "production"})
    assert promote_v2.status_code == 200
    assert promote_v2.json()["stage"] == "production"

    get_v1 = client.get("/api/v1/models/ranker/versions/1")
    assert get_v1.status_code == 200
    assert get_v1.json()["stage"] == "archived"

    list_prod = client.get("/api/v1/models/ranker/versions", params={"stage": "production"})
    assert list_prod.status_code == 200
    assert len(list_prod.json()) == 1
    assert list_prod.json()[0]["version"] == 2


def test_artifact_upload_download(client):
    client.post("/api/v1/models", json={"name": "ranker"})
    client.post("/api/v1/models/ranker/versions", json={})

    upload_resp = client.post(
        "/api/v1/models/ranker/versions/1/artifacts",
        files={"file": ("../model.bin", b"binary-content", "application/octet-stream")},
    )
    assert upload_resp.status_code == 200
    assert upload_resp.json()["artifact_uri"] == "s3://models/ranker/v1/model.bin"

    download_resp = client.get("/api/v1/models/ranker/versions/1/artifacts/model.bin", follow_redirects=False)
    assert download_resp.status_code == 307
    assert download_resp.headers["location"] == "http://fake-minio/ranker/v1/model.bin"


def test_artifact_size_limit(client):
    settings = get_settings()
    original_limit = settings.artifact_max_bytes
    settings.artifact_max_bytes = 3
    try:
        client.post("/api/v1/models", json={"name": "ranker"})
        client.post("/api/v1/models/ranker/versions", json={})
        upload_resp = client.post(
            "/api/v1/models/ranker/versions/1/artifacts",
            files={"file": ("model.bin", b"abcd", "application/octet-stream")},
        )
        assert upload_resp.status_code == 413
    finally:
        settings.artifact_max_bytes = original_limit
