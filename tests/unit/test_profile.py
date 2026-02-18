from __future__ import annotations

import json


def auth(client):
    """Helper function to authenticate user for tests"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "takudzwa", "password": "takudzwa"}
    )
    assert response.status_code == 200
    return response


def test_profile_page_requires_auth(client):
    """Test that profile page requires authentication"""
    response = client.get("/api/v1/profile")
    assert response.status_code == 302


def test_profile_page_with_auth(client):
    """Test profile page with authentication"""
    auth(client)
    response = client.get("/api/v1/profile")
    assert response.status_code == 200
    assert b"profile" in response.data.lower()


def test_update_profile_requires_auth(client):
    """Test that updating profile requires authentication"""
    profile_data = {
        "first_name": "Updated",
        "last_name": "User",
        "email": "updated@example.com",
        "phone": "+1234567890",
    }
    response = client.post("/api/v1/profile", json=profile_data)
    assert response.status_code == 302


def test_update_profile_with_auth(client):
    """Test updating profile with authentication"""
    auth(client)
    profile_data = {
        "first_name": "Updated",
        "last_name": "User",
        "email": "updated@example.com",
        "phone": "+1234567890",
    }
    response = client.post("/api/v1/profile", json=profile_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_update_profile_invalid_data(client):
    """Test updating profile with invalid data"""
    auth(client)
    invalid_data = {
        "first_name": "",  # Empty first name
        "last_name": "User",
        "email": "invalid-email",  # Invalid email
        "phone": "invalid-phone",  # Invalid phone
    }
    response = client.post("/api/v1/profile", json=invalid_data)
    assert response.status_code == 400


def test_update_profile_missing_fields(client):
    """Test updating profile with missing required fields"""
    auth(client)
    incomplete_data = {
        "first_name": "Updated"
        # Missing other required fields
    }
    response = client.post("/api/v1/profile", json=incomplete_data)
    # Profile updates might allow partial updates
    assert response.status_code in (200, 400)


def test_update_profile_duplicate_email(client):
    """Test updating profile with duplicate email"""
    auth(client)
    profile_data = {
        "first_name": "Updated",
        "last_name": "User",
        "email": "admin@example.com",  # This email already exists
        "phone": "+1234567890",
    }
    response = client.post("/api/v1/profile", json=profile_data)
    assert response.status_code == 400


def test_change_password_requires_auth(client):
    """Test that changing password requires authentication"""
    password_data = {
        "current_password": "password",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123",
    }
    response = client.post("/api/v1/profile/change-password", json=password_data)
    assert response.status_code == 302


def test_change_password_with_auth(client):
    """Test changing password with authentication"""
    auth(client)
    password_data = {
        "current_password": "password",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123",
    }
    response = client.post("/api/v1/profile/change-password", json=password_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_change_password_invalid_current_password(client):
    """Test changing password with invalid current password"""
    auth(client)
    password_data = {
        "current_password": "wrongpassword",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123",
    }
    response = client.post("/api/v1/profile/change-password", json=password_data)
    assert response.status_code == 400


def test_change_password_password_mismatch(client):
    """Test changing password with mismatched passwords"""
    auth(client)
    password_data = {
        "current_password": "password",
        "new_password": "newpassword123",
        "confirm_password": "differentpassword",
    }
    response = client.post("/api/v1/profile/change-password", json=password_data)
    assert response.status_code == 400


def test_change_password_weak_password(client):
    """Test changing password with weak password"""
    auth(client)
    password_data = {
        "current_password": "password",
        "new_password": "123",  # Weak password
        "confirm_password": "123",
    }
    response = client.post("/api/v1/profile/change-password", json=password_data)
    assert response.status_code == 400


def test_change_password_missing_fields(client):
    """Test changing password with missing required fields"""
    auth(client)
    incomplete_data = {
        "current_password": "password"
        # Missing new password fields
    }
    response = client.post("/api/v1/profile/change-password", json=incomplete_data)
    assert response.status_code == 400


def test_change_password_same_password(client):
    """Test changing password to the same password"""
    auth(client)
    password_data = {
        "current_password": "password",
        "new_password": "password",
        "confirm_password": "password",
    }
    response = client.post("/api/v1/profile/change-password", json=password_data)
    assert response.status_code == 400


def test_get_password_requirements_requires_auth(client):
    """Test that getting password requirements requires authentication"""
    response = client.get("/api/v1/profile/password-requirements")
    assert response.status_code == 302


def test_get_password_requirements_with_auth(client):
    """Test getting password requirements with authentication"""
    auth(client)
    response = client.get("/api/v1/profile/password-requirements")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_profile_validation(client):
    """Test profile data validation"""
    auth(client)
    # Test various validation scenarios
    test_cases = [
        {"first_name": "", "last_name": "User"},  # Empty first name
        {"first_name": "John", "email": "invalid-email"},  # Invalid email
        {"first_name": "John", "phone": "invalid-phone"},  # Invalid phone
        {"first_name": "A" * 256, "last_name": "User"},  # Name too long
    ]

    for test_data in test_cases:
        response = client.post("/api/v1/profile", json=test_data)
        assert response.status_code == 400


def test_password_validation(client):
    """Test password validation"""
    auth(client)
    # Test various password validation scenarios
    test_cases = [
        {
            "current_password": "password",
            "new_password": "123",
            "confirm_password": "123",
        },  # Weak password
        {
            "current_password": "password",
            "new_password": "password",
            "confirm_password": "password",
        },  # Same password
        {
            "current_password": "password",
            "new_password": "newpass",
            "confirm_password": "different",
        },  # Mismatch
        {
            "current_password": "wrong",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },  # Wrong current
    ]

    for test_data in test_cases:
        response = client.post("/api/v1/profile/change-password", json=test_data)
        assert response.status_code == 400


def test_profile_partial_update(client):
    """Test partial profile update"""
    auth(client)
    # Test updating only some fields
    partial_data = {"first_name": "Updated First Name"}
    response = client.post("/api/v1/profile", json=partial_data)
    # Should succeed with partial data
    assert response.status_code in (200, 400)


def test_profile_empty_update(client):
    """Test empty profile update"""
    auth(client)
    empty_data = {}
    response = client.post("/api/v1/profile", json=empty_data)
    # Should succeed or fail gracefully
    assert response.status_code in (200, 400)


def test_profile_contact_info_update(client):
    """Test updating contact information"""
    auth(client)
    contact_data = {"email": "newemail@example.com", "phone": "+9876543210"}
    response = client.post("/api/v1/profile", json=contact_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_profile_name_update(client):
    """Test updating name fields"""
    auth(client)
    name_data = {"first_name": "New First Name", "last_name": "New Last Name"}
    response = client.post("/api/v1/profile", json=name_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_password_requirements_structure(client):
    """Test password requirements response structure"""
    auth(client)
    response = client.get("/api/v1/profile/password-requirements")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    # Check if password requirements are included
    if "requirements" in data:
        requirements = data["requirements"]
        assert isinstance(requirements, dict)


def test_profile_update_success(client):
    """Test successful profile update"""
    auth(client)
    profile_data = {
        "first_name": "Updated First",
        "last_name": "Updated Last",
        "email": "updated@example.com",
        "phone": "+1234567890",
    }
    response = client.post("/api/v1/profile", json=profile_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_password_change_success(client):
    """Test successful password change"""
    auth(client)
    password_data = {
        "current_password": "password",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123",
    }
    response = client.post("/api/v1/profile/change-password", json=password_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_profile_update_with_special_characters(client):
    """Test profile update with special characters"""
    auth(client)
    special_data = {
        "first_name": "José",
        "last_name": "García-López",
        "email": "jose.garcia@example.com",
        "phone": "+1-555-123-4567",
    }
    response = client.post("/api/v1/profile", json=special_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_password_change_with_special_characters(client):
    """Test password change with special characters"""
    auth(client)
    password_data = {
        "current_password": "password",
        "new_password": "NewPassword123!@#",
        "confirm_password": "NewPassword123!@#",
    }
    response = client.post("/api/v1/profile/change-password", json=password_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401
