"""Mobile API routes blueprint for owner and tenant mobile app."""
from flask import Blueprint

# Create mobile API blueprint
mobile_api = Blueprint('mobile_api', __name__, url_prefix='/api/mobile')

# Import routes to register them with the blueprint
from . import auth, units, notifications, tickets
