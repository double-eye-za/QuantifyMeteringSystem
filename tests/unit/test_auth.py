from __future__ import annotations


def test_login_logout_flow(client):
    # login
    r = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )
    assert r.status_code == 200
    # access protected
    r2 = client.get("/api/v1/estates")
    assert r2.status_code in (200, 204)
    # logout
    r3 = client.post("/api/v1/auth/logout")
    assert r3.status_code == 200
    # protected should now be 401
    r4 = client.get("/api/v1/estates")
    assert r4.status_code == 401


def test_change_password_requires_login(client):
    r = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "password", "new_password": "newpass"},
    )
    assert r.status_code == 401


def test_change_password_flow(client):
    # login
    r = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "password"}
    )
    assert r.status_code == 200

    # change password
    r2 = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "password", "new_password": "newpass"},
    )
    assert r2.status_code == 200

    # login with new password
    r3 = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "newpass"}
    )
    assert r3.status_code == 200

    # change it back to original to avoid impacting other tests
    r4 = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "newpass", "new_password": "password"},
    )
    assert r4.status_code == 200

    # logout
    r5 = client.post("/api/v1/auth/logout")
    assert r5.status_code == 200
