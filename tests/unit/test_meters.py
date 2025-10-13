from __future__ import annotations


def auth(client):
    client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )


def test_meters_list_and_detail(client):
    auth(client)
    # list
    r = client.get("/api/v1/meters")
    assert r.status_code == 200
    # detail not found
    r2 = client.get("/api/v1/meters/999999")
    assert r2.status_code == 404


def test_meter_readings_list(client):
    auth(client)
    r = client.get("/api/v1/meters/1/readings")
    # meter may not exist, expect 200 with empty data or 404 depending on implementation
    assert r.status_code in (200, 404)
