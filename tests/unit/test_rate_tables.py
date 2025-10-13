from __future__ import annotations


def auth(client):
    client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )


def test_rate_tables_list_and_detail(client):
    auth(client)
    r = client.get("/api/v1/rate-tables")
    assert r.status_code == 200
    r2 = client.get("/api/v1/rate-tables/999999")
    assert r2.status_code in (200, 404)


def test_rate_tables_filtering(client):
    auth(client)
    r = client.get("/api/v1/rate-tables?utility_type=electricity&is_active=true")
    assert r.status_code == 200
