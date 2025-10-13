from __future__ import annotations


def auth(client):
    client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )


def test_transactions_list_and_detail(client):
    auth(client)
    r = client.get("/api/v1/transactions")
    assert r.status_code == 200
    r2 = client.get("/api/v1/transactions/999999")
    assert r2.status_code == 404


def test_transactions_reverse(client):
    auth(client)
    # reversing non-existent txn should be 404
    r = client.post("/api/v1/transactions/999999/reverse", json={"reason": "test"})
    assert r.status_code == 404
