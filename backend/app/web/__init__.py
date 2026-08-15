from flask import Blueprint

web_bp = Blueprint("web", __name__)

from .dashboard import dashboard_bp
from .devices import devices_bp
from .networks import networks_bp
from .connections import connections_bp
from .topology import topology_bp
from .discovery import discovery_bp

web_bp.register_blueprint(dashboard_bp)
web_bp.register_blueprint(devices_bp)
web_bp.register_blueprint(networks_bp)
web_bp.register_blueprint(connections_bp)
web_bp.register_blueprint(topology_bp)
web_bp.register_blueprint(discovery_bp)
