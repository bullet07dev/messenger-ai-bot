import logging
logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self, config):
        self.config = config
        self.client = None
        if config.is_supabase_enabled():
            try:
                from supabase import create_client
                self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                logger.info("Supabase connected")
            except Exception as e:
                logger.error(f"Supabase connection failed: {e}")
                self.client = None
        else:
            logger.info("Supabase not configured - using in-memory fallback")
    
    # Bookings
    def save_booking(self, booking):
        if self.client:
            try:
                self.client.table("bookings").upsert(booking, on_conflict="booking_id").execute()
                return True
            except Exception as e:
                logger.error(f"Supabase save booking error: {e}")
        return False
    
    def get_booking(self, booking_id):
        if self.client:
            try:
                res = self.client.table("bookings").select("*").eq("booking_id", booking_id.upper()).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase get booking error: {e}")
        return None
    
    def list_user_bookings(self, user_id):
        if self.client:
            try:
                res = self.client.table("bookings").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()
                return res.data or []
            except Exception as e:
                logger.error(f"Supabase list bookings error: {e}")
        return []
    
    def get_all_bookings(self, page_id=None, limit=50):
        if self.client:
            try:
                query = self.client.table("bookings").select("*").order("created_at", desc=True).limit(limit)
                if page_id:
                    query = query.eq("page_id", page_id)
                res = query.execute()
                return res.data or []
            except Exception as e:
                logger.error(f"Supabase get all bookings error: {e}")
        return []
    
    # User states (for booking flow)
    def save_state(self, user_id, state):
        if self.client:
            try:
                self.client.table("user_states").upsert({"user_id": user_id, "state": state}, on_conflict="user_id").execute()
            except Exception as e:
                logger.error(f"Supabase save state error: {e}")
    
    def get_state(self, user_id):
        if self.client:
            try:
                res = self.client.table("user_states").select("state").eq("user_id", user_id).execute()
                if res.data:
                    return res.data[0].get("state")
            except Exception as e:
                logger.error(f"Supabase get state error: {e}")
        return None
    
    def clear_state(self, user_id):
        if self.client:
            try:
                self.client.table("user_states").delete().eq("user_id", user_id).execute()
            except Exception as e:
                logger.error(f"Supabase clear state error: {e}")
    
    # Logs for observability (enterprise)
    def log_message(self, log_data):
        if self.client:
            try:
                self.client.table("message_logs").insert(log_data).execute()
            except Exception as e:
                logger.error(f"Supabase log error: {e}")
    
    # User language preference
    def save_user_lang(self, user_id, lang):
        if self.client:
            try:
                self.client.table("users").upsert({"user_id": user_id, "preferred_lang": lang}, on_conflict="user_id").execute()
            except:
                pass
    
    def get_user_lang(self, user_id):
        if self.client:
            try:
                res = self.client.table("users").select("preferred_lang").eq("user_id", user_id).execute()
                if res.data:
                    return res.data[0].get("preferred_lang")
            except:
                pass
        return None