from __future__ import annotations


def auth(client):
    client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )


def test_reports_and_system(client):
    auth(client)
    r1 = client.get("/api/v1/reports/estate-consumption")
    assert r1.status_code == 200
    r2 = client.get("/api/v1/reports/reconciliation")
    assert r2.status_code == 200
    r3 = client.get("/api/v1/reports/low-credit")
    assert r3.status_code == 200
    r4 = client.get("/api/v1/reports/revenue")
    assert r4.status_code == 200
    r5 = client.get("/api/v1/system/health")
    assert r5.status_code == 200
