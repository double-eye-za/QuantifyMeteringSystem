from __future__ import annotations


def auth(client):
    client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )


def test_notifications_list(client):
    auth(client)
    r = client.get("/api/v1/notifications")
    assert r.status_code == 200
