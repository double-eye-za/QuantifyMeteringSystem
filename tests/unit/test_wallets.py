from __future__ import annotations


def auth(client):
    client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )


def test_wallets_endpoints(client):
    auth(client)
    # expect 404 on non-existing wallet
    r = client.get("/api/v1/wallets/1")
    assert r.status_code in (200, 404)

    # topup on missing wallet should not 500
    r2 = client.post(
        "/api/v1/wallets/1/topup", json={"amount": 100, "payment_method": "eft"}
    )
    assert r2.status_code in (201, 404)

    # pending list
    r3 = client.get("/api/v1/wallets/1/pending-transactions")
    assert r3.status_code in (200, 404)


def test_wallets_topup_validation(client):
    auth(client)
    # invalid payload should not 500
    r = client.post("/api/v1/wallets/1/topup", json={})
    assert r.status_code in (400, 404)
