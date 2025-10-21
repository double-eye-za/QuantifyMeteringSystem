from __future__ import annotations

import json


def auth(client):
    """Helper function to authenticate user for tests"""
    response = client.post(
        "/api/v1/auth/login", json={"username": "takudzwa", "password": "takudzwa"}
    )
    assert response.status_code == 200
    return response


def test_list_transactions_requires_auth(client):
    """Test that listing transactions requires authentication"""
    response = client.get("/api/v1/transactions")
    assert response.status_code == 302


def test_list_transactions_with_auth(client):
    """Test listing transactions with authentication"""
    auth(client)
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_list_transactions_with_pagination(client):
    """Test listing transactions with pagination"""
    auth(client)
    response = client.get("/api/v1/transactions?page=1&per_page=10")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_list_transactions_with_filters(client):
    """Test listing transactions with filters"""
    auth(client)
    response = client.get(
        "/api/v1/transactions?wallet_id=1&transaction_type=credit&status=completed"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_list_transactions_with_date_range(client):
    """Test listing transactions with date range"""
    auth(client)
    response = client.get(
        "/api/v1/transactions?start_date=2024-01-01&end_date=2024-12-31"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_list_transactions_with_search(client):
    """Test listing transactions with search"""
    auth(client)
    response = client.get("/api/v1/transactions?search=topup")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_get_transaction_requires_auth(client):
    """Test that getting transaction requires authentication"""
    response = client.get("/api/v1/transactions/1")
    assert response.status_code == 302


def test_get_transaction_with_auth(client):
    """Test getting transaction with authentication"""
    auth(client)
    response = client.get("/api/v1/transactions/1")
    # May return 200 with empty data or 404 if transaction doesn't exist
    assert response.status_code in (200, 404)


def test_get_transaction_not_found(client):
    """Test getting non-existent transaction"""
    auth(client)
    response = client.get("/api/v1/transactions/999999")
    assert response.status_code == 404


def test_reverse_transaction_requires_auth(client):
    """Test that reversing transaction requires authentication"""
    reverse_data = {"reason": "Test reversal"}
    response = client.post("/api/v1/transactions/1/reverse", json=reverse_data)
    assert response.status_code == 302


def test_reverse_transaction_with_auth(client):
    """Test reversing transaction with authentication"""
    auth(client)
    reverse_data = {"reason": "Test reversal"}
    response = client.post("/api/v1/transactions/1/reverse", json=reverse_data)
    # May fail due to missing transaction or business logic, but should not be 401
    assert response.status_code != 401


def test_reverse_transaction_not_found(client):
    """Test reversing non-existent transaction"""
    auth(client)
    reverse_data = {"reason": "Test reversal"}
    response = client.post("/api/v1/transactions/999999/reverse", json=reverse_data)
    assert response.status_code == 404


def test_reverse_transaction_missing_reason(client):
    """Test reversing transaction without reason"""
    auth(client)
    reverse_data = {}
    response = client.post("/api/v1/transactions/1/reverse", json=reverse_data)
    assert response.status_code == 400


def test_reverse_transaction_empty_reason(client):
    """Test reversing transaction with empty reason"""
    auth(client)
    reverse_data = {"reason": ""}
    response = client.post("/api/v1/transactions/1/reverse", json=reverse_data)
    assert response.status_code == 400


def test_reverse_transaction_long_reason(client):
    """Test reversing transaction with very long reason"""
    auth(client)
    reverse_data = {
        "reason": "A" * 1000  # Very long reason
    }
    response = client.post("/api/v1/transactions/1/reverse", json=reverse_data)
    # Should succeed or fail with validation error, not auth error
    assert response.status_code != 401


def test_transactions_list_structure(client):
    """Test transactions list response structure"""
    auth(client)
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    # Check if transactions are included
    if "transactions" in data:
        transactions = data["transactions"]
        assert isinstance(transactions, list)


def test_transaction_detail_structure(client):
    """Test transaction detail response structure"""
    auth(client)
    response = client.get("/api/v1/transactions/1")
    if response.status_code == 200:
        data = response.get_json()
        assert isinstance(data, dict)
        # Check if transaction details are included
        if "transaction" in data:
            transaction = data["transaction"]
            assert isinstance(transaction, dict)


def test_transactions_with_different_types(client):
    """Test transactions with different types"""
    auth(client)
    transaction_types = ["credit", "debit", "topup", "payment", "refund"]

    for txn_type in transaction_types:
        response = client.get(f"/api/v1/transactions?transaction_type={txn_type}")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)


def test_transactions_with_different_statuses(client):
    """Test transactions with different statuses"""
    auth(client)
    statuses = ["pending", "completed", "failed", "cancelled", "reversed"]

    for status in statuses:
        response = client.get(f"/api/v1/transactions?status={status}")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)


def test_transactions_with_amount_range(client):
    """Test transactions with amount range"""
    auth(client)
    response = client.get("/api/v1/transactions?min_amount=10.0&max_amount=100.0")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_transactions_with_multiple_filters(client):
    """Test transactions with multiple filters"""
    auth(client)
    response = client.get(
        "/api/v1/transactions?wallet_id=1&transaction_type=credit&status=completed&start_date=2024-01-01&end_date=2024-12-31"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_transactions_pagination_boundaries(client):
    """Test transactions pagination boundaries"""
    auth(client)
    # Test with very large page number
    response = client.get("/api/v1/transactions?page=999999&per_page=10")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)

    # Test with very large per_page
    response = client.get("/api/v1/transactions?page=1&per_page=1000")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_transactions_sorting(client):
    """Test transactions sorting"""
    auth(client)
    sort_options = ["date", "amount", "type", "status"]

    for sort_by in sort_options:
        response = client.get(f"/api/v1/transactions?sort_by={sort_by}&sort_order=desc")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)


def test_transactions_export_format(client):
    """Test transactions export format"""
    auth(client)
    response = client.get("/api/v1/transactions?export=csv")
    assert response.status_code == 200
    # Should return CSV format or JSON with export data
    data = response.get_json()
    assert isinstance(data, dict)


def test_transaction_reversal_business_logic(client):
    """Test transaction reversal business logic"""
    auth(client)
    # Test reversing a transaction that might not be reversible
    reverse_data = {"reason": "Business logic test"}
    response = client.post("/api/v1/transactions/1/reverse", json=reverse_data)
    # Should succeed or fail with business logic error, not auth error
    assert response.status_code != 401


def test_transactions_with_wallet_filter(client):
    """Test transactions filtered by wallet"""
    auth(client)
    response = client.get("/api/v1/transactions?wallet_id=1")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_transactions_with_user_filter(client):
    """Test transactions filtered by user"""
    auth(client)
    response = client.get("/api/v1/transactions?user_id=1")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_transactions_with_estate_filter(client):
    """Test transactions filtered by estate"""
    auth(client)
    response = client.get("/api/v1/transactions?estate_id=1")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_transactions_with_unit_filter(client):
    """Test transactions filtered by unit"""
    auth(client)
    response = client.get("/api/v1/transactions?unit_id=1")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)


def test_transactions_metadata(client):
    """Test transactions metadata"""
    auth(client)
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
    # Check if metadata is included
    if "total" in data:
        assert isinstance(data["total"], int)
    if "page" in data:
        assert isinstance(data["page"], int)
    if "per_page" in data:
        assert isinstance(data["per_page"], int)


def test_transaction_reversal_validation(client):
    """Test transaction reversal validation"""
    auth(client)
    # Test various validation scenarios
    test_cases = [
        {"reason": ""},  # Empty reason
        {"reason": "A" * 2000},  # Very long reason
        {"reason": None},  # Null reason
    ]

    for test_data in test_cases:
        response = client.post("/api/v1/transactions/1/reverse", json=test_data)
        assert response.status_code == 400


def test_transactions_complex_query(client):
    """Test complex transactions query"""
    auth(client)
    response = client.get(
        "/api/v1/transactions?wallet_id=1&transaction_type=credit&status=completed&start_date=2024-01-01&end_date=2024-12-31&min_amount=10.0&max_amount=1000.0&sort_by=date&sort_order=desc&page=1&per_page=20"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, dict)
