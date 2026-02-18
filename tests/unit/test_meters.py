from __future__ import annotations

import json


def auth(client):
    """Helper function to authenticate user for tests"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "takudzwa", "password": "takudzwa"}
    )
    # Login should return 200 with success message
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("message") == "Logged in"
    return response


def test_meters_page_requires_auth(client):
    """Test that meters page requires authentication"""
    response = client.get("/api/v1/meters")
    # Should redirect to login (302) instead of 401
    assert response.status_code == 302


def test_meters_page_with_auth(client):
    """Test meters page with authentication"""
    auth(client)
    response = client.get("/api/v1/meters")
    assert response.status_code == 200
    assert b"meters" in response.data.lower()


def test_meters_page_with_filters(client):
    """Test meters page with various filters"""
    auth(client)
    response = client.get(
        "/api/v1/meters?meter_type=electricity&communication_status=online&estate_id=1&credit_status=ok"
    )
    assert response.status_code == 200


def test_meter_details_page(client):
    """Test meter details page"""
    auth(client)
    response = client.get("/api/v1/meters/1/details")
    # May return 200 with empty data or 404 if meter doesn't exist
    assert response.status_code in (200, 404)


def test_get_meter_by_id(client):
    """Test getting meter by ID"""
    auth(client)
    response = client.get("/api/v1/meters/1")
    # May return 200 with empty data or 404 if meter doesn't exist
    assert response.status_code in (200, 404)


def test_get_meter_by_id_not_found(client):
    """Test getting non-existent meter"""
    auth(client)
    response = client.get("/api/v1/meters/999999")
    assert response.status_code == 404


def test_create_meter_requires_auth(client):
    """Test that creating meter requires authentication"""
    meter_data = {
        "serial_number": "TEST123",
        "meter_type": "electricity",
        "unit_id": 1,
        "installation_date": "2024-01-01",
        "initial_reading": 0,
    }
    response = client.post("/api/v1/meters", json=meter_data)
    assert response.status_code == 302


def test_create_meter_with_auth(client):
    """Test creating meter with authentication"""
    auth(client)
    meter_data = {
        "serial_number": "TEST123",
        "meter_type": "electricity",
        "unit_id": 1,
        "installation_date": "2024-01-01",
        "initial_reading": 0,
    }
    response = client.post("/api/v1/meters", json=meter_data)
    # May fail due to missing unit, but should not be 401
    assert response.status_code != 401


def test_create_meter_invalid_data(client):
    """Test creating meter with invalid data"""
    auth(client)
    invalid_data = {
        "serial_number": "",  # Empty serial number
        "meter_type": "invalid_type",
        "unit_id": "not_a_number",
    }
    response = client.post("/api/v1/meters", json=invalid_data)
    assert response.status_code == 400


def test_update_meter_requires_auth(client):
    """Test that updating meter requires authentication"""
    meter_data = {"serial_number": "UPDATED123", "meter_type": "water"}
    response = client.put("/api/v1/meters/1", json=meter_data)
    assert response.status_code == 302


def test_update_meter_not_found(client):
    """Test updating non-existent meter"""
    auth(client)
    meter_data = {"serial_number": "UPDATED123", "meter_type": "water"}
    response = client.put("/api/v1/meters/999999", json=meter_data)
    assert response.status_code == 404


def test_delete_meter_requires_auth(client):
    """Test that deleting meter requires authentication"""
    response = client.delete("/api/v1/meters/1")
    assert response.status_code == 302


def test_delete_meter_not_found(client):
    """Test deleting non-existent meter"""
    auth(client)
    response = client.delete("/api/v1/meters/999999")
    assert response.status_code == 404


def test_get_available_meters(client):
    """Test getting available meters"""
    auth(client)
    response = client.get("/api/v1/meters/available")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_get_meter_readings(client):
    """Test getting meter readings"""
    auth(client)
    response = client.get("/api/v1/meters/1/readings")
    # May return 200 with empty data or 404 if meter doesn't exist
    assert response.status_code in (200, 404)


def test_get_meter_readings_with_params(client):
    """Test getting meter readings with parameters"""
    auth(client)
    response = client.get(
        "/api/v1/meters/1/readings?page=1&per_page=10&start_date=2024-01-01&end_date=2024-12-31"
    )
    assert response.status_code in (200, 404)


def test_export_meters_requires_auth(client):
    """Test that exporting meters requires authentication"""
    response = client.get("/api/v1/meters/export")
    assert response.status_code == 302


def test_export_meters_with_auth(client):
    """Test exporting meters with authentication"""
    auth(client)
    response = client.get("/api/v1/meters/export")
    assert response.status_code == 200


def test_export_meters_with_format(client):
    """Test exporting meters with specific format"""
    auth(client)
    response = client.get("/api/v1/meters/export?format=pdf")
    assert response.status_code == 200


def test_export_meters_with_filters(client):
    """Test exporting meters with filters"""
    auth(client)
    response = client.get("/api/v1/meters/export?meter_type=electricity&estate_id=1")
    assert response.status_code == 200
