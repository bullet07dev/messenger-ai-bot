from flask import Blueprint, jsonify, request
from ..config import Config
from .supabase_client import SupabaseService

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/bookings', methods=['GET'])
def get_bookings():
    config = Config()
    # Simple auth via query param ?key=VERIFY_TOKEN
    key = request.args.get('key')
    if key != config.VERIFY_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    supabase = SupabaseService(config)
    from .booking_manager import BookingManager
    bm = BookingManager(supabase)
    
    page_id = request.args.get('page_id')
    bookings = bm.get_all_bookings(page_id)
    
    return jsonify({"count": len(bookings), "bookings": bookings}), 200

@admin_bp.route('/api/admin/stats', methods=['GET'])
def get_stats():
    config = Config()
    key = request.args.get('key')
    if key != config.VERIFY_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    supabase = SupabaseService(config)
    from .booking_manager import BookingManager
    bm = BookingManager(supabase)
    all_bookings = bm.get_all_bookings()
    
    # Simple stats
    stats = {
        "total": len(all_bookings),
        "by_type": {},
        "by_status": {},
        "by_lang": {}
    }
    for b in all_bookings:
        t = b.get('type', 'unknown')
        stats["by_type"][t] = stats["by_type"].get(t, 0) + 1
        s = b.get('status', 'pending')
        stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
    
    if supabase.client:
        try:
            logs = supabase.client.table("message_logs").select("model_used, lang").limit(100).execute()
            if logs.data:
                for log in logs.data:
                    model = log.get('model_used', 'unknown')
                    stats["by_status"][model] = stats["by_status"].get(model, 0) + 1
                    lang = log.get('lang', 'unknown')
                    stats["by_lang"][lang] = stats["by_lang"].get(lang, 0) + 1
        except:
            pass
    
    return jsonify(stats), 200