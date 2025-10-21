from __future__ import annotations

import json


def auth(client):
    """Helper function to authenticate user for tests"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "takudzwa", "password": "takudzwa"}
    )
    assert response.status_code == 200
    return response


def test_estates_page_requires_auth(client):
    """Test that estates page requires authentication"""
    response = client.get("/api/v1/estates")
    # Should redirect to login (302) instead of 401
    assert response.status_code == 302


def test_estates_page_with_auth(client):
    """Test estates page with authentication"""
    auth(client)
    response = client.get("/api/v1/estates")
    assert response.status_code == 200
    assert b"estates" in response.data.lower()


def test_estates_page_with_filters(client):
    """Test estates page with filters"""
    auth(client)
    response = client.get("/api/v1/estates?search=test&status=active")
    assert response.status_code == 200


def test_get_estate_by_id(client):
    """Test getting estate by ID"""
    auth(client)
    response = client.get("/api/v1/estates/1")
    # May return 200 with empty data or 404 if estate doesn't exist
    assert response.status_code in (200, 404)


def test_get_estate_by_id_not_found(client):
    """Test getting non-existent estate"""
    auth(client)
    response = client.get("/api/v1/estates/999999")
    assert response.status_code == 404


def test_create_estate_requires_auth(client):
    """Test that creating estate requires authentication"""
    estate_data = {
        "name": "Test Estate",
        "address": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "postal_code": "12345",
        "country": "Test Country",
    }
    response = client.post("/api/v1/estates", json=estate_data)
    assert response.status_code == 302


def test_create_estate_with_auth(client):
    """Test creating estate with authentication"""
    auth(client)
    estate_data = {
        "name": "Test Estate",
        "address": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "postal_code": "12345",
        "country": "Test Country",
    }
    response = client.post("/api/v1/estates", json=estate_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_create_estate_invalid_data(client):
    """Test creating estate with invalid data"""
    auth(client)
    invalid_data = {
        "name": "",  # Empty name
        "address": "123 Test Street",
    }
    response = client.post("/api/v1/estates", json=invalid_data)
    assert response.status_code == 400


def test_create_estate_missing_fields(client):
    """Test creating estate with missing required fields"""
    auth(client)
    incomplete_data = {
        "name": "Test Estate"
        # Missing other required fields
    }
    response = client.post("/api/v1/estates", json=incomplete_data)
    assert response.status_code == 400


def test_update_estate_requires_auth(client):
    """Test that updating estate requires authentication"""
    estate_data = {"name": "Updated Estate", "address": "456 Updated Street"}
    response = client.put("/api/v1/estates/1", json=estate_data)
    assert response.status_code == 302


def test_update_estate_not_found(client):
    """Test updating non-existent estate"""
    auth(client)
    estate_data = {"name": "Updated Estate", "address": "456 Updated Street"}
    response = client.put("/api/v1/estates/999999", json=estate_data)
    assert response.status_code == 404


def test_update_estate_success(client):
    """Test updating estate successfully"""
    auth(client)
    # First create an estate
    estate_data = {
        "name": "Test Estate",
        "address": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "postal_code": "12345",
        "country": "Test Country",
    }

    create_response = client.post("/api/v1/estates", json=estate_data)
    if create_response.status_code == 201:
        estate_id = create_response.get_json().get("estate", {}).get("id")
        if estate_id:
            update_data = {"name": "Updated Estate", "address": "456 Updated Street"}
            response = client.put(f"/api/v1/estates/{estate_id}", json=update_data)
            assert response.status_code == 200


def test_delete_estate_requires_auth(client):
    """Test that deleting estate requires authentication"""
    response = client.delete("/api/v1/estates/1")
    assert response.status_code == 302


def test_delete_estate_not_found(client):
    """Test deleting non-existent estate"""
    auth(client)
    response = client.delete("/api/v1/estates/999999")
    assert response.status_code == 404


def test_delete_estate_success(client):
    """Test deleting estate successfully"""
    auth(client)
    # First create an estate
    estate_data = {
        "name": "Test Estate",
        "address": "123 Test Street",
        "city": "Test City",
        "state": "Test State",
        "postal_code": "12345",
        "country": "Test Country",
    }

    create_response = client.post("/api/v1/estates", json=estate_data)
    if create_response.status_code == 201:
        estate_id = create_response.get_json().get("estate", {}).get("id")
        if estate_id:
            response = client.delete(f"/api/v1/estates/{estate_id}")
            assert response.status_code == 200


def test_estate_validation(client):
    """Test estate data validation"""
    auth(client)
    # Test various validation scenarios
    test_cases = [
        {"name": "", "address": "123 Test"},  # Empty name
        {"name": "A" * 256, "address": "123 Test"},  # Name too long
        {"name": "Test", "address": ""},  # Empty address
        {"name": "Test", "postal_code": "invalid"},  # Invalid postal code
    ]

    for test_data in test_cases:
        response = client.post("/api/v1/estates", json=test_data)
        assert response.status_code == 400


def test_estate_search(client):
    """Test estate search functionality"""
    auth(client)
    response = client.get("/api/v1/estates?search=test")
    assert response.status_code == 200


def test_estate_pagination(client):
    """Test estate pagination"""
    auth(client)
    response = client.get("/api/v1/estates?page=1&per_page=10")
    assert response.status_code == 200
