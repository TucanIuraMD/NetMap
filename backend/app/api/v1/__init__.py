from flask import Blueprint

api_v1 = Blueprint("api_v1", __name__)

from .sites import sites_bp
from .networks import networks_bp
from .devices import devices_bp
from .interfaces import interfaces_bp
from .ip_addresses import ip_addresses_bp
from .ports import ports_bp
from .services import services_bp
from .connections import connections_bp
from .discovery import discovery_bp

api_v1.register_blueprint(sites_bp)
api_v1.register_blueprint(networks_bp)
api_v1.register_blueprint(devices_bp)
api_v1.register_blueprint(interfaces_bp)
api_v1.register_blueprint(ip_addresses_bp)
api_v1.register_blueprint(ports_bp)
api_v1.register_blueprint(services_bp)
api_v1.register_blueprint(connections_bp)
api_v1.register_blueprint(discovery_bp)
