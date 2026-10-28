import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Facebook
    PAGE_TOKENS = {
        # Supports multi-page via env: PAGE_TOKEN_1, PAGE_ID_1, etc or single PAGE_ACCESS_TOKEN
        os.getenv("PAGE_ID", "default"): os.getenv("PAGE_ACCESS_TOKEN", "")
    }
    # Also parse PAGE_TOKEN_1, PAGE_TOKEN_2 for multi-tenant
    for i in range(1, 11):
        pid = os.getenv(f"PAGE_ID_{i}")
        ptoken = os.getenv(f"PAGE_TOKEN_{i}")
        if pid and ptoken:
            PAGE_TOKENS[pid] = ptoken
    
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "jeafred_bot_123")
    APP_SECRET = os.getenv("APP_SECRET", "")  # For signature verification (enterprise security)
    
    # AI - Fixed models
    GEMINI_KEY = os.getenv("GEMINI_KEY", "")
    GROQ_KEY = os.getenv("GROQ_KEY", "")
    GEMINI_MODELS = ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-2.0-flash-exp"]
    GROQ_MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "gemma2-9b-it", "llama3-8b-8192"]  # last as fallback
    
    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    
    # Upstash Redis (optional)
    UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL", "")
    UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN", "")
    
    # Qdrant (optional)
    QDRANT_URL = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    
    # Business
    BUSINESS_TYPE = os.getenv("BUSINESS_TYPE", "multi")  # resort, photographer, product, multi
    BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Jeafred Photography & Resort")
    BUSINESS_HOURS = os.getenv("BUSINESS_HOURS", "8AM-10PM")
    
    # Human keywords
    HUMAN_KEYWORDS = ["human", "agent", "staff", "manager", "tawag", "tawagan", "kailangan ko tao", "need human"]
    
    # Rooms & Packages - Config driven (can move to DB later)
    RESORT_ROOMS = {
        "standard": {"name": "Standard Room (2 pax)", "price": 2500, "pax": 2},
        "deluxe": {"name": "Deluxe Room (3 pax)", "price": 3500, "pax": 3},
        "family": {"name": "Family Villa (5 pax)", "price": 5000, "pax": 5},
        "barkada": {"name": "Barkada Package (10 pax)", "price": 8000, "pax": 10},
    }
    WEDDING_PACKAGES = {
        "gold": {"name": "Gold Package", "price": 40000, "team": "2 Photo, 3 Video, 1 SDE", "referral": 2000},
        "silver": {"name": "Silver Package", "price": 25000, "team": "1 Photo, 2 Video", "referral": 1500},
        "bronze": {"name": "Bronze Package", "price": 18000, "team": "1 Photo, 1 Video", "referral": 1000},
    }
    BASE_RATES = {
        "photographer": {"name": "Base Photographer 4hrs", "price": 3500, "referral": 1000},
        "videographer": {"name": "Videographer 4hrs", "price": 7000, "referral": 1000},
        "sde": {"name": "SDE Whole Day", "price": 6500, "referral": 500},
        "drone": {"name": "Drone Whole Day", "price": 5000, "referral": 500},
        "prenup": {"name": "PreNup & Save the Date", "price": 8000, "referral": 500},
    }
    ALBUMS = {
        "30": {"name": "Album 30 pages", "price": 5500},
        "20": {"name": "Album 20 pages", "price": 4000},
        "10": {"name": "Album 10 pages", "price": 3000},
    }
    
    def get_business_config(self, page_id):
        # In enterprise, this would query Supabase pages table
        # For now, return default with business type from env
        return {
            "name": self.BUSINESS_NAME,
            "type": self.BUSINESS_TYPE,
            "hours": self.BUSINESS_HOURS,
            "page_id": page_id
        }
    
    def get_page_token(self, page_id):
        return self.PAGE_TOKENS.get(page_id) or self.PAGE_TOKENS.get("default") or os.getenv("PAGE_ACCESS_TOKEN", "")
    
    def validate(self):
        if not self.get_page_token("default") and not any(self.PAGE_TOKENS.values()):
            print("WARNING: No PAGE_ACCESS_TOKEN set!")
    
    def is_supabase_enabled(self):
        return bool(self.SUPABASE_URL and self.SUPABASE_KEY)