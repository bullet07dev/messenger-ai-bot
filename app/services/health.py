from flask import Blueprint, jsonify
from ..config import Config
from .supabase_client import SupabaseService
import requests

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    config = Config()
    supabase = SupabaseService(config)
    
    status = {
        "status": "ok",
        "version": "enterprise-v2",
        "supabase": "connected" if supabase.client else "not_configured (using memory)",
        "groq": "configured" if config.GROQ_KEY.startswith("gsk_") else "not_configured",
        "gemini": "configured" if config.GEMINI_KEY.startswith("AIza") else f"invalid_format (starts with {config.GROQ_KEY[:4] if config.GEMINI_KEY else 'empty'})",
        "page_tokens": len([v for v in config.PAGE_TOKENS.values() if v]),
        "business_type": config.BUSINESS_TYPE
    }
    
    # Test Groq
    if config.GROQ_KEY.startswith("gsk_"):
        try:
            r = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {config.GROQ_KEY}"}, timeout=5)
            status["groq_test"] = "ok" if r.status_code == 200 else f"error {r.status_code}"
        except Exception as e:
            status["groq_test"] = f"error {e}"
    
    return jsonify(status), 200

@health_bp.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Jeafred Enterprise Bot V2 - Running", "health": "/health", "webhook": "/api/messenger/webhook"}), 200