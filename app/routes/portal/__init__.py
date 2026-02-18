"""Portal routes blueprint for owner/tenant web portal."""
from flask import Blueprint

# Create portal blueprint
portal = Blueprint('portal', __name__, url_prefix='/portal')

# Import routes to register them with the blueprint
from . import dashboard
from . import units
from . import meters
from . import wallet
from . import messages
from . import notifications
from . import tickets
from . import profile
