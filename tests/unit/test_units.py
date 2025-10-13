from __future__ import annotations


def auth(client):
    client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )


def test_units_crud(client):
    auth(client)
    # need an estate first
    est = client.post("/api/v1/estates", json={"code": "E2", "name": "E2"}).get_json()[
        "data"
    ]
    estate_id = est["id"]

    # create unit
    payload = {
        "estate_id": estate_id,
        "unit_number": "A-101",
        "bedrooms": 2,
    }
    r = client.post("/api/v1/units", json=payload)
    assert r.status_code == 201
    unit_id = r.get_json()["data"]["id"]

    # get
    r2 = client.get(f"/api/v1/units/{unit_id}")
    assert r2.status_code == 200

    # list
    r3 = client.get(f"/api/v1/units?estate_id={estate_id}")
    assert r3.status_code == 200

    # update
    r4 = client.put(f"/api/v1/units/{unit_id}", json={"bedrooms": 3})
    assert r4.status_code == 200
    assert r4.get_json()["data"]["bedrooms"] == 3
