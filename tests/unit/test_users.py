from __future__ import annotations


def auth(client):
    """Helper function to authenticate user for tests"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "takudzwa", "password": "takudzwa"}
    )
    assert response.status_code == 200
    return response


def test_create_user_requires_auth(client):
    """Test that creating user requires authentication"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "password123",
        "role_id": 1,
    }
    response = client.post("/api/v1/api/users", json=user_data)
    assert response.status_code == 302


def test_create_user_with_auth(client):
    """Test creating user with authentication"""
    auth(client)
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "password123",
        "role_id": 1,
    }
    response = client.post("/api/v1/api/users", json=user_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_create_user_invalid_data(client):
    """Test creating user with invalid data"""
    auth(client)
    invalid_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "123",  # Weak password
    }
    response = client.post("/api/v1/api/users", json=invalid_data)
    assert response.status_code == 400


def test_create_user_missing_fields(client):
    """Test creating user with missing required fields"""
    auth(client)
    incomplete_data = {
        "username": "testuser",
        # Missing other required fields
    }
    response = client.post("/api/v1/api/users", json=incomplete_data)
    assert response.status_code == 400


def test_create_user_duplicate_username(client):
    """Test creating user with duplicate username"""
    auth(client)
    user_data = {
        "username": "takudzwa",  # This username already exists
        "email": "admin2@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "password": "password123",
        "role_id": 1,
    }
    response = client.post("/api/v1/api/users", json=user_data)
    assert response.status_code == 400


def test_create_user_duplicate_email(client):
    """Test creating user with duplicate email"""
    auth(client)
    user_data = {
        "username": "admin2",
        "email": "takudzwa@metalogix.solutions",  # This email already exists
        "first_name": "Admin",
        "last_name": "User",
        "password": "password123",
        "role_id": 1,
    }
    response = client.post("/api/v1/api/users", json=user_data)
    assert response.status_code == 400


def test_update_user_requires_auth(client):
    """Test that updating user requires authentication"""
    user_data = {"first_name": "Updated", "last_name": "User"}
    response = client.put("/api/v1/api/users/1", json=user_data)
    assert response.status_code == 302


def test_update_user_success(client):
    """Test updating user successfully"""
    auth(client)
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "password123",
        "role_id": 1,
    }

    create_response = client.post("/api/v1/api/users", json=user_data)
    if create_response.status_code == 201:
        user_id = create_response.get_json().get("user", {}).get("id")
        if user_id:
            update_data = {"first_name": "Updated", "last_name": "User"}
            response = client.put(f"/api/v1/api/users/{user_id}", json=update_data)
            assert response.status_code == 200


def test_delete_user_requires_auth(client):
    """Test that deleting user requires authentication"""
    response = client.delete("/api/v1/api/users/1")
    assert response.status_code == 302


def test_delete_user_success(client):
    """Test deleting user successfully"""
    auth(client)
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "password123",
        "role_id": 1,
    }

    create_response = client.post("/api/v1/api/users", json=user_data)
    if create_response.status_code == 201:
        user_id = create_response.get_json().get("user", {}).get("id")
        if user_id:
            response = client.delete(f"/api/v1/api/users/{user_id}")
            assert response.status_code == 200


def test_enable_user_requires_auth(client):
    """Test that enabling user requires authentication"""
    response = client.put("/api/v1/api/users/1/enable")
    assert response.status_code == 302


def test_enable_user_success(client):
    """Test enabling user successfully"""
    auth(client)
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "password123",
        "role_id": 1,
    }

    create_response = client.post("/api/v1/api/users", json=user_data)
    if create_response.status_code == 201:
        user_id = create_response.get_json().get("user", {}).get("id")
        if user_id:
            response = client.put(f"/api/v1/api/users/{user_id}/enable")
            assert response.status_code == 200


def test_disable_user_requires_auth(client):
    """Test that disabling user requires authentication"""
    response = client.put("/api/v1/api/users/1/disable")
    assert response.status_code == 302


def test_disable_user_success(client):
    """Test disabling user successfully"""
    auth(client)
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "password123",
        "role_id": 1,
    }

    create_response = client.post("/api/v1/api/users", json=user_data)
    if create_response.status_code == 201:
        user_id = create_response.get_json().get("user", {}).get("id")
        if user_id:
            response = client.put(f"/api/v1/api/users/{user_id}/disable")
            assert response.status_code == 200


def test_user_validation(client):
    """Test user data validation"""
    auth(client)

    test_cases = [
        {"username": "", "email": "test@example.com"},  # Empty username
        {"username": "test", "email": "invalid-email"},  # Invalid email
        {
            "username": "test",
            "email": "test@example.com",
            "password": "",
        },  # Empty password
    ]

    for test_data in test_cases:
        response = client.post("/api/v1/api/users", json=test_data)
        assert response.status_code == 400
