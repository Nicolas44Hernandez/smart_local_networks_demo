""" App initialization module."""

import logging
from logging.config import dictConfig
from os import path
import yaml
from flask import Flask
from flask_cors import CORS

from .managers.wifi_bands_manager import wifi_bands_manager_service
from .managers.smart_band_manager import band_5GHz_manager_service
from .application import poll_and_predict_manager_service
from .rest_api.wifi_controler import bp as wifi_controler_bp
from .rest_api.wifi_5GHz_on_off_controler import bp as wifi_5GHz_on_off_controler_bp
from .extension import api
from .common import ServerException, handle_server_exception

logger = logging.getLogger(__name__)


def create_app(
    config_dir: str = path.join(path.dirname(path.abspath(__file__)), "config"),
):
    """Create the Flask app"""

    # Create app Flask
    app = Flask("Server Box")
    cors = CORS(app)

    # Get configuration files
    app_config = path.join(config_dir, "server-config.yml")
    logging_config = path.join(config_dir, "logging-config.yml")

    # Load logging configuration and configure flask application logger
    with open(logging_config) as stream:
        dictConfig(yaml.full_load(stream))

    logger.info("App config file: %s", app_config)

    # Load configuration
    app.config.from_file(app_config, load=yaml.full_load)

    # Register extensions
    register_extensions(app)
    # Register blueprints for REST API
    register_blueprints(app)
    logger.info("App ready!!")

    return app


def register_extensions(app: Flask):
    """Initialize all extensions"""

    # Initialize REST APIs.
    #
    # The spec_kwargs dict is used to generate the OpenAPI document that describes our APIs.
    # The securitySchemes field defines the security scheme used to protect our APIs.
    #   - BasicAuth  allows to authenticate a user with a login and a password.
    #   - BearerAuth allows to authenticate a user using a token (the /login API allows to a user
    #     to retrieve a valid token).

    api.init_app(
        app,
        spec_kwargs={
            "info": {"description": "`Orchestrator` OpenAPI 3.0 specification."},
            "components": {
                "securitySchemes": {
                    "basicAuth": {"type": "http", "scheme": "basic"},
                    "tokenAuth": {"type": "http", "scheme": "bearer"},
                },
            },
        },
    )
    # Wifi bands manager extension
    wifi_bands_manager_service.init_app(app=app)
    # Wifi 5GHz on/off manager extension
    band_5GHz_manager_service.init_app(app=app)
    # predicot service extension
    poll_and_predict_manager_service.init_app(app=app)


def register_blueprints(app: Flask):
    """Store App APIs blueprints."""
    # Register error handler
    app.register_error_handler(ServerException, handle_server_exception)
    # Register REST blueprints
    api.register_blueprint(wifi_controler_bp)
    api.register_blueprint(wifi_5GHz_on_off_controler_bp)

