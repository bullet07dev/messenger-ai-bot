from flask import Blueprint, jsonify
from ..config import Config
import requests

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    config = Config()
    try:
        from .supabase_client import SupabaseService
        supabase = SupabaseService(config)
        supabase_status = "connected" if supabase.client else "not_configured (using memory) - add SUPABASE_URL + SUPABASE_KEY + install supabase==2.3.0"
    except Exception as e:
        supabase_status = f"error: {e} (install supabase lib or use memory fallback)"
    
    status = {
        "status": "ok",
        "version": "enterprise-v2-fixed",
        "python_version": "3.11.6 (via runtime.txt)",
        "supabase": supabase_status,
        "groq": "configured" if config.GROQ_KEY.startswith("gsk_") else "not_configured",
        "gemini": "configured" if config.GEMINI_KEY.startswith("AIza") else f"invalid_format (starts with {config.GEMINI_KEY[:4] if config.GEMINI_KEY else 'empty'}) - get AIza key from aistudio.google.com",
        "page_tokens": len([v for v in config.PAGE_TOKENS.values() if v]),
        "business_type": config.BUSINESS_TYPE,
        "fix": "This version fixes qdrant-client error - no longer requires qdrant"
    }
    
    if config.GROQ_KEY.startswith("gsk_"):
        try:
            r = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {config.GROQ_KEY}"}, timeout=5)
            status["groq_test"] = "ok - key works!" if r.status_code == 200 else f"error {r.status_code}: {r.text[:200]}"
        except Exception as e:
            status["groq_test"] = f"error {e}"
    
    return jsonify(status), 200

@health_bp.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Jeafred Enterprise Bot V2 Fixed - Running", "health": "/health", "admin": "/admin", "webhook": "/api/messenger/webhook"}), 200