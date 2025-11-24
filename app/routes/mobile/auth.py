"""Mobile app authentication endpoints."""
from __future__ import annotations

import jwt
import datetime
from functools import wraps
from flask import jsonify, request, current_app
from typing import Optional, Tuple

from ...services.mobile_users import (
    authenticate_mobile_user,
    change_password,
    get_user_units,
    get_mobile_user_by_id,
)
from ...models import MobileUser, Person
from . import mobile_api


def generate_token(mobile_user: MobileUser) -> str:
    """
    Generate JWT token for mobile user.

    Args:
        mobile_user: MobileUser object

    Returns:
        JWT token string
    """
    payload = {
        'user_id': mobile_user.id,
        'person_id': mobile_user.person_id,
        'phone_number': mobile_user.phone_number,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30),  # Token expires in 30 days
        'iat': datetime.datetime.utcnow()
    }

    # Use Flask secret key for JWT encoding
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict or None if invalid
    """
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_mobile_auth(f):
    """
    Decorator to require mobile authentication for endpoints.

    Extracts JWT token from Authorization header and validates it.
    Adds mobile_user to kwargs.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'error': 'Missing authorization header',
                'message': 'Please provide Authorization header with Bearer token'
            }), 401

        # Extract token (format: "Bearer <token>")
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'error': 'Invalid authorization header',
                'message': 'Authorization header must be in format: Bearer <token>'
            }), 401

        token = parts[1]

        # Decode token
        payload = decode_token(token)
        if not payload:
            return jsonify({
                'error': 'Invalid or expired token',
                'message': 'Please login again'
            }), 401

        # Get mobile user
        mobile_user = get_mobile_user_by_id(payload['user_id'])
        if not mobile_user:
            return jsonify({
                'error': 'User not found',
                'message': 'User account no longer exists'
            }), 401

        if not mobile_user.is_active:
            return jsonify({
                'error': 'Account inactive',
                'message': 'Your account has been deactivated'
            }), 403

        # Add mobile_user to kwargs
        kwargs['mobile_user'] = mobile_user

        return f(*args, **kwargs)

    return decorated_function


@mobile_api.post("/auth/login")
def login():
    """
    Mobile app login endpoint.

    Request body:
        {
            "phone_number": "+27821234567",
            "password": "MyPass123"
        }

    Response:
        {
            "token": "eyJ0eXAiOiJKV1QiLCJ...",
            "user": {
                "id": 1,
                "person_id": 4,
                "phone_number": "+27821234567",
                "password_must_change": false
            },
            "person": {
                "id": 4,
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe"
            },
            "units": [
                {
                    "unit_id": 10,
                    "unit_number": "101",
                    "estate_id": 1,
                    "estate_name": "Sunset Estate",
                    "role": "owner"
                }
            ],
            "password_must_change": false
        }
    """
    payload = request.get_json(force=True) or {}

    # Validate required fields
    if not payload.get('phone_number') or not payload.get('password'):
        return jsonify({
            'error': 'Missing required fields',
            'message': 'phone_number and password are required'
        }), 400

    # Authenticate user
    success, result = authenticate_mobile_user(
        phone_number=payload['phone_number'],
        password=payload['password']
    )

    if not success:
        return jsonify({
            'error': 'Authentication failed',
            'message': result.get('message', 'Invalid phone number or password')
        }), result.get('code', 401)

    mobile_user = result

    # Generate JWT token
    token = generate_token(mobile_user)

    # Get user's units
    units = get_user_units(mobile_user.person_id)

    # Get person details
    person = mobile_user.person

    return jsonify({
        'token': token,
        'user': mobile_user.to_dict(),
        'person': {
            'id': person.id,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'full_name': person.full_name,
            'phone': person.phone,
            'email': person.email,
        },
        'units': units,
        'password_must_change': mobile_user.password_must_change
    }), 200


@mobile_api.post("/auth/change-password")
@require_mobile_auth
def change_user_password(mobile_user: MobileUser):
    """
    Change mobile user password.

    Requires authentication.

    Request body:
        {
            "current_password": "OldPass123",
            "new_password": "NewPass456"
        }

    Response:
        {
            "message": "Password changed successfully"
        }
    """
    payload = request.get_json(force=True) or {}

    # Validate required fields
    if not payload.get('new_password'):
        return jsonify({
            'error': 'Missing required fields',
            'message': 'new_password is required'
        }), 400

    # Change password
    success, result = change_password(
        mobile_user=mobile_user,
        new_password=payload['new_password'],
        current_password=payload.get('current_password')
    )

    if not success:
        return jsonify({
            'error': 'Password change failed',
            'message': result.get('message', 'Failed to change password')
        }), result.get('code', 400)

    return jsonify(result), 200


@mobile_api.get("/auth/user")
@require_mobile_auth
def get_current_user(mobile_user: MobileUser):
    """
    Get current authenticated user profile.

    Requires authentication.

    Response:
        {
            "user": {
                "id": 1,
                "person_id": 4,
                "phone_number": "+27821234567",
                "password_must_change": false
            },
            "person": {
                "id": 4,
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe"
            }
        }
    """
    person = mobile_user.person

    return jsonify({
        'user': mobile_user.to_dict(),
        'person': {
            'id': person.id,
            'first_name': person.first_name,
            'last_name': person.last_name,
            'full_name': person.full_name,
            'phone': person.phone,
            'email': person.email,
        }
    }), 200


@mobile_api.get("/auth/units")
@require_mobile_auth
def get_units(mobile_user: MobileUser):
    """
    Get all units the authenticated user can access.

    Requires authentication.

    Response:
        {
            "units": [
                {
                    "unit_id": 10,
                    "unit_number": "101",
                    "estate_id": 1,
                    "estate_name": "Sunset Estate",
                    "role": "owner",
                    "is_primary": true,
                    "ownership_percentage": 100.0
                },
                {
                    "unit_id": 15,
                    "unit_number": "205",
                    "estate_id": 1,
                    "estate_name": "Sunset Estate",
                    "role": "tenant",
                    "is_primary": false,
                    "monthly_rent": 8500.0,
                    "lease_start_date": "2024-01-01",
                    "lease_end_date": "2024-12-31"
                }
            ]
        }
    """
    units = get_user_units(mobile_user.person_id)

    return jsonify({
        'units': units
    }), 200
