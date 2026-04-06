def test_models_crud_flow(client):
    create_resp = client.post(
        "/api/v1/models",
        json={"name": "ranker", "description": "v1", "team": "mlds_180"},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["name"] == "ranker"

    duplicate_resp = client.post("/api/v1/models", json={"name": "ranker"})
    assert duplicate_resp.status_code == 409

    get_resp = client.get("/api/v1/models/ranker")
    assert get_resp.status_code == 200
    assert get_resp.json()["team"] == "mlds_180"

    list_resp = client.get("/api/v1/models", params={"team": "mlds_180"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    patch_resp = client.patch("/api/v1/models/ranker", json={"description": "updated", "team": "reco"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["description"] == "updated"
    assert patch_resp.json()["team"] == "reco"

    patch_empty = client.patch("/api/v1/models/ranker", json={})
    assert patch_empty.status_code == 200
    assert patch_empty.json()["description"] == "updated"
    assert patch_empty.json()["team"] == "reco"

    delete_resp = client.delete("/api/v1/models/ranker")
    assert delete_resp.status_code == 204

    not_found_resp = client.get("/api/v1/models/ranker")
    assert not_found_resp.status_code == 404
