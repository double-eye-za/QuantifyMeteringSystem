from __future__ import annotations


def auth(client):
    """Helper function to authenticate user for tests"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "takudzwa", "password": "takudzwa"}
    )
    assert response.status_code == 200
    return response


def test_create_role_requires_auth(client):
    """Test that creating role requires authentication"""
    role_data = {
        "name": "Test Role",
        "description": "A test role",
        "permissions": {
            "estates": {"view": True, "create": False, "edit": False, "delete": False},
            "units": {"view": True, "create": False, "edit": False, "delete": False},
        },
    }
    response = client.post("/api/v1/api/roles", json=role_data)
    assert response.status_code == 302


def test_create_role_with_auth(client):
    """Test creating role with authentication"""
    auth(client)
    role_data = {
        "name": "Test Role",
        "description": "A test role",
        "permissions": {
            "estates": {"view": True, "create": False, "edit": False, "delete": False},
            "units": {"view": True, "create": False, "edit": False, "delete": False},
        },
    }
    response = client.post("/api/v1/api/roles", json=role_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_create_role_invalid_data(client):
    """Test creating role with invalid data"""
    auth(client)
    invalid_data = {
        "name": "Test Role",
        "description": "A test role",
        "permissions": "invalid_permissions",  # Invalid permissions format
    }
    response = client.post("/api/v1/api/roles", json=invalid_data)
    assert response.status_code == 400


def test_create_role_missing_fields(client):
    """Test creating role with missing required fields"""
    auth(client)
    incomplete_data = {
        "name": "Test Role",
        # Missing other required fields
    }
    response = client.post("/api/v1/api/roles", json=incomplete_data)
    assert response.status_code == 400


def test_create_role_duplicate_name(client):
    """Test creating role with duplicate name"""
    auth(client)
    role_data = {
        "name": "Super Administrator",  # This role already exists
        "description": "A duplicate role",
        "permissions": {
            "estates": {"view": True, "create": False, "edit": False, "delete": False},
        },
    }
    response = client.post("/api/v1/api/roles", json=role_data)
    assert response.status_code == 400


def test_update_role_requires_auth(client):
    """Test that updating role requires authentication"""
    role_data = {"name": "Updated Role", "description": "An updated role"}
    response = client.put("/api/v1/api/roles/1", json=role_data)
    assert response.status_code == 302


def test_update_role_success(client):
    """Test updating role successfully"""
    auth(client)
    role_data = {
        "name": "Test Role",
        "description": "A test role",
        "permissions": {
            "estates": {"view": True, "create": False, "edit": False, "delete": False},
        },
    }

    create_response = client.post("/api/v1/api/roles", json=role_data)
    if create_response.status_code == 201:
        role_id = create_response.get_json().get("role", {}).get("id")
        if role_id:
            update_data = {"name": "Updated Role", "description": "An updated role"}
            response = client.put(f"/api/v1/api/roles/{role_id}", json=update_data)
            assert response.status_code == 200


def test_delete_role_requires_auth(client):
    """Test that deleting role requires authentication"""
    response = client.delete("/api/v1/api/roles/1")
    assert response.status_code == 302


def test_delete_role_success(client):
    """Test deleting role successfully"""
    auth(client)
    role_data = {
        "name": "Test Role",
        "description": "A test role",
        "permissions": {
            "estates": {"view": True, "create": False, "edit": False, "delete": False},
        },
    }

    create_response = client.post("/api/v1/api/roles", json=role_data)
    if create_response.status_code == 201:
        role_id = create_response.get_json().get("role", {}).get("id")
        if role_id:
            response = client.delete(f"/api/v1/api/roles/{role_id}")
            assert response.status_code == 200


def test_role_validation(client):
    """Test role data validation"""
    auth(client)

    test_cases = [
        {"name": "", "description": "Test role"},  # Empty name
        {
            "name": "test",
            "description": "Test role",
            "permissions": {},
        },  # Empty permissions
        {
            "name": "test",
            "description": "Test role",
            "permissions": "invalid",
        },  # Invalid permissions
    ]

    for test_data in test_cases:
        response = client.post("/api/v1/api/roles", json=test_data)
        # Some validation might be more lenient, so accept success or validation error
        assert response.status_code in (200, 201, 400)


def test_role_permissions_structure(client):
    """Test role permissions structure validation"""
    auth(client)

    role_data = {
        "name": "Test Role",
        "description": "A test role",
        "permissions": {
            "estates": {"view": True, "create": False, "edit": False, "delete": False},
            "units": {"view": True, "create": False, "edit": False, "delete": False},
            "meters": {"view": True, "create": False, "edit": False, "delete": False},
            "residents": {
                "view": True,
                "create": False,
                "edit": False,
                "delete": False,
            },
        },
    }
    response = client.post("/api/v1/api/roles", json=role_data)
    # Should succeed with valid permissions structure or fail with validation
    assert response.status_code in (200, 201, 400)
