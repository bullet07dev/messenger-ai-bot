from flask import Flask
from .config import Config

def create_app():
    app = Flask(__name__)
    Config().validate()
    from .services.messenger import messenger_bp
    from .services.admin_api import admin_bp
    from .services.health import health_bp
    from .services.admin_static import admin_static_bp
    app.register_blueprint(messenger_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_static_bp)
    return app