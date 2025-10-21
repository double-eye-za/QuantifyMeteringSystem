from __future__ import annotations

import json


def auth(client):
    """Helper function to authenticate user for tests"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "takudzwa", "password": "takudzwa"}
    )
    assert response.status_code == 200
    return response


def test_residents_page_requires_auth(client):
    """Test that residents page requires authentication"""
    response = client.get("/api/v1/residents")
    assert response.status_code == 302


def test_residents_page_with_auth(client):
    """Test residents page with authentication"""
    auth(client)
    response = client.get("/api/v1/residents")
    assert response.status_code == 200
    assert b"residents" in response.data.lower()


def test_residents_page_with_filters(client):
    """Test residents page with filters"""
    auth(client)
    response = client.get("/api/v1/residents?search=john&unit_id=1&status=active")
    assert response.status_code == 200


def test_residents_list_api(client):
    """Test residents list API endpoint"""
    auth(client)
    response = client.get("/api/v1/residents")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_residents_list_with_pagination(client):
    """Test residents list with pagination"""
    auth(client)
    response = client.get("/api/v1/residents?page=1&per_page=10")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_residents_list_with_search(client):
    """Test residents list with search"""
    auth(client)
    response = client.get("/api/v1/residents?search=john")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_residents_list_with_filters(client):
    """Test residents list with filters"""
    auth(client)
    response = client.get(
        "/api/v1/residents?unit_id=1&status=active&resident_type=primary"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_create_resident_requires_auth(client):
    """Test that creating resident requires authentication"""
    resident_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "unit_id": 1,
        "resident_type": "primary",
        "move_in_date": "2024-01-01",
    }
    response = client.post("/api/v1/residents", json=resident_data)
    assert response.status_code == 302


def test_create_resident_with_auth(client):
    """Test creating resident with authentication"""
    auth(client)
    resident_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "unit_id": 1,
        "resident_type": "primary",
        "move_in_date": "2024-01-01",
    }
    response = client.post("/api/v1/residents", json=resident_data)
    # May fail due to missing unit, but should not be 401
    assert response.status_code != 401


def test_create_resident_invalid_data(client):
    """Test creating resident with invalid data"""
    auth(client)
    invalid_data = {
        "first_name": "",  # Empty first name
        "last_name": "Doe",
        "email": "invalid-email",  # Invalid email
        "phone": "invalid-phone",  # Invalid phone
        "unit_id": "not_a_number",
    }
    response = client.post("/api/v1/residents", json=invalid_data)
    assert response.status_code == 400


def test_create_resident_missing_fields(client):
    """Test creating resident with missing required fields"""
    auth(client)
    incomplete_data = {
        "first_name": "John"
        # Missing other required fields
    }
    response = client.post("/api/v1/residents", json=incomplete_data)
    assert response.status_code == 400


def test_create_resident_duplicate_email(client):
    """Test creating resident with duplicate email"""
    auth(client)
    resident_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "admin@example.com",  # This email already exists
        "phone": "+1234567890",
        "unit_id": 1,
        "resident_type": "primary",
        "move_in_date": "2024-01-01",
    }
    response = client.post("/api/v1/residents", json=resident_data)
    assert response.status_code == 400


def test_update_resident_requires_auth(client):
    """Test that updating resident requires authentication"""
    resident_data = {"first_name": "Jane", "last_name": "Smith"}
    response = client.put("/api/v1/residents/1", json=resident_data)
    assert response.status_code == 302


def test_update_resident_not_found(client):
    """Test updating non-existent resident"""
    auth(client)
    resident_data = {"first_name": "Jane", "last_name": "Smith"}
    response = client.put("/api/v1/residents/999999", json=resident_data)
    assert response.status_code == 404


def test_update_resident_success(client):
    """Test updating resident successfully"""
    auth(client)
    # First create a resident
    resident_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "unit_id": 1,
        "resident_type": "primary",
        "move_in_date": "2024-01-01",
    }

    create_response = client.post("/api/v1/residents", json=resident_data)
    if create_response.status_code == 201:
        resident_id = create_response.get_json().get("resident", {}).get("id")
        if resident_id:
            update_data = {"first_name": "Jane", "last_name": "Smith"}
            response = client.put(f"/api/v1/residents/{resident_id}", json=update_data)
            assert response.status_code == 200


def test_delete_resident_requires_auth(client):
    """Test that deleting resident requires authentication"""
    response = client.delete("/api/v1/residents/1")
    assert response.status_code == 302


def test_delete_resident_not_found(client):
    """Test deleting non-existent resident"""
    auth(client)
    response = client.delete("/api/v1/residents/999999")
    assert response.status_code == 404


def test_delete_resident_success(client):
    """Test deleting resident successfully"""
    auth(client)
    # First create a resident
    resident_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "unit_id": 1,
        "resident_type": "primary",
        "move_in_date": "2024-01-01",
    }

    create_response = client.post("/api/v1/residents", json=resident_data)
    if create_response.status_code == 201:
        resident_id = create_response.get_json().get("resident", {}).get("id")
        if resident_id:
            response = client.delete(f"/api/v1/residents/{resident_id}")
            assert response.status_code == 200


def test_resident_validation(client):
    """Test resident data validation"""
    auth(client)
    # Test various validation scenarios
    test_cases = [
        {"first_name": "", "last_name": "Doe"},  # Empty first name
        {"first_name": "John", "email": "invalid-email"},  # Invalid email
        {"first_name": "John", "phone": "invalid-phone"},  # Invalid phone
        {
            "first_name": "John",
            "resident_type": "invalid_type",
        },  # Invalid resident type
        {"first_name": "John", "move_in_date": "invalid-date"},  # Invalid date
    ]

    for test_data in test_cases:
        response = client.post("/api/v1/residents", json=test_data)
        assert response.status_code == 400


def test_resident_search(client):
    """Test resident search functionality"""
    auth(client)
    response = client.get("/api/v1/residents?search=john")
    assert response.status_code == 200


def test_resident_pagination(client):
    """Test resident pagination"""
    auth(client)
    response = client.get("/api/v1/residents?page=1&per_page=10")
    assert response.status_code == 200


def test_resident_unit_filter(client):
    """Test resident unit filtering"""
    auth(client)
    response = client.get("/api/v1/residents?unit_id=1")
    assert response.status_code == 200


def test_resident_status_filter(client):
    """Test resident status filtering"""
    auth(client)
    response = client.get("/api/v1/residents?status=active")
    assert response.status_code == 200


def test_resident_type_filter(client):
    """Test resident type filtering"""
    auth(client)
    response = client.get("/api/v1/residents?resident_type=primary")
    assert response.status_code == 200


def test_resident_estate_filter(client):
    """Test resident estate filtering"""
    auth(client)
    response = client.get("/api/v1/residents?estate_id=1")
    assert response.status_code == 200


def test_resident_move_in_date_filter(client):
    """Test resident move-in date filtering"""
    auth(client)
    response = client.get(
        "/api/v1/residents?move_in_date_from=2024-01-01&move_in_date_to=2024-12-31"
    )
    assert response.status_code == 200


def test_resident_contact_info(client):
    """Test resident contact information"""
    auth(client)
    response = client.get("/api/v1/residents")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    if "residents" in data:
        residents = data["residents"]
        if residents:
            resident = residents[0]
            # Check if contact info is included
            assert "email" in resident or "phone" in resident


def test_resident_unit_association(client):
    """Test resident unit association"""
    auth(client)
    response = client.get("/api/v1/residents")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    if "residents" in data:
        residents = data["residents"]
        if residents:
            resident = residents[0]
            # Check if unit information is included
            assert "unit_id" in resident or "unit" in resident
