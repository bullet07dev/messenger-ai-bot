from flask import Flask
from .services.messenger import messenger_bp
import logging
def create_app():
    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    app.register_blueprint(messenger_bp)
    @app.route('/')
    def home():
        import os
        return {"status": "live", "service": "Jeafred Photography Booking Bot - Custom Rates", "type": os.environ.get("BUSINESS_TYPE", "photographer"), "name": os.environ.get("BUSINESS_NAME", "Jeafred Photography")}, 200
    @app.route('/health')
    def health():
        import os
        return {"ok": True, "type": os.environ.get("BUSINESS_TYPE"), "has_token": bool(os.environ.get("PAGE_TOKEN"))}, 200
    return app
