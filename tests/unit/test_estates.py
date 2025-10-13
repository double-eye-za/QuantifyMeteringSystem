from __future__ import annotations


def auth(client):
    client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )


def test_estates_crud(client):
    auth(client)
    # list empty
    r = client.get("/api/v1/estates")
    assert r.status_code == 200
    assert r.get_json().get("data") == []

    # create
    payload = {
        "code": "EST001",
        "name": "Test Estate",
        "city": "City",
        "total_units": 0,
    }
    r2 = client.post("/api/v1/estates", json=payload)
    assert r2.status_code == 201
    estate_id = r2.get_json()["data"]["id"]

    # get
    r3 = client.get(f"/api/v1/estates/{estate_id}")
    assert r3.status_code == 200
    assert r3.get_json()["data"]["name"] == "Test Estate"

    # update
    r4 = client.put(f"/api/v1/estates/{estate_id}", json={"name": "Updated Estate"})
    assert r4.status_code == 200
    assert r4.get_json()["data"]["name"] == "Updated Estate"

    # delete
    r5 = client.delete(f"/api/v1/estates/{estate_id}")
    assert r5.status_code == 200
