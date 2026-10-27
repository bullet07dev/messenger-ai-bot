import os, json

class Config:
    VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "jeafred_bot_123").strip()
    PAGE_TOKEN = os.environ.get("PAGE_TOKEN", "").strip()
    BUSINESS_TYPE = os.environ.get("BUSINESS_TYPE", "photographer").strip().lower()
    BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "Jeafred Photography").strip()
    BUSINESS_HOURS = os.environ.get("BUSINESS_HOURS", "8AM-10PM Daily").strip()
    LOCATION = os.environ.get("LOCATION", "Guimba, Nueva Ecija").strip()
    
    MULTI_PAGE_TOKENS_RAW = os.environ.get("MULTI_PAGE_TOKENS", "").strip()
    MULTI_PAGE_TOKENS = {}
    if MULTI_PAGE_TOKENS_RAW:
        try:
            MULTI_PAGE_TOKENS = json.loads(MULTI_PAGE_TOKENS_RAW)
        except:
            pass
    BUSINESS_CONFIGS_RAW = os.environ.get("BUSINESS_CONFIGS", "").strip()
    BUSINESS_CONFIGS = {}
    if BUSINESS_CONFIGS_RAW:
        try:
            BUSINESS_CONFIGS = json.loads(BUSINESS_CONFIGS_RAW)
        except:
            pass

    GROQ_KEY = os.environ.get("GROQ_KEY", "").strip()
    GEMINI_KEY = os.environ.get("GEMINI_KEY", "").strip()
    GEMINI_MODELS = ["gemini-1.5-flash", "gemini-1.5-flash-latest"]
    GROQ_MODELS = ["llama3-8b-8192", "llama-3.1-8b-instant", "gemma2-9b-it"]
    
    HUMAN_KEYWORDS = ["human", "agent", "person", "tawag", "tao", "staff", "manager", "owner"]

    # ===== YOUR REAL TIE-UP RATES =====
    BASE_RATES = {
        "photographer": {"price": 3500, "hours": "4 hrs", "name": "Base Photographer (4 hrs event)", "referral": 1000},
        "videographer": {"price": 7000, "hours": "4 hrs", "name": "Base Videographer (4 hrs, shoot & edit)", "referral": 1000},
        "sde": {"price": 6500, "hours": "whole day", "name": "Base Same Day Editor (whole day)", "referral": 500},
        "drone": {"price": 5000, "hours": "whole day", "name": "Base Drone Pilot (whole day)", "referral": 500},
        "prenup": {"price": 8000, "hours": "whole day", "name": "PreNup & Save the Date (photo + video, whole day)", "referral": 500},
    }
    
    WEDDING_PACKAGES = {
        "gold": {
            "price": 40000,
            "referral": 2000,
            "team": "2 Photographers, 3 Videographers, 1 SDE Editor",
            "name": "Package Gold - 40k",
            "inclusions": "Prenup (unli enhanced), Save the Date Video (2-5min musical/narration with aerials), Wedding Photo (unli enhanced), Wedding Video (Full Doc with aerials), Same Day Edit video"
        },
        "silver": {
            "price": 25000,
            "referral": 1500,
            "team": "1 Photographer, 2 Videographers",
            "name": "Package Silver - 25k",
            "inclusions": "Prenup (unli enhanced + RAW), Save the Date Video (2-5min with aerials), Wedding Photo (unli enhanced), Wedding Video (Complete Highlights with aerials)"
        },
        "bronze": {
            "price": 18000,
            "referral": 1000,
            "team": "1 Photographer, 1 Videographer",
            "name": "Package Bronze - 18k",
            "inclusions": "Prenup (unli enhanced + RAW), Save the Date Video (2-5min musical/narration), Wedding Photo (unli enhanced), Wedding Video (Wedding Highlights)"
        },
    }
    
    ADDONS = {
        "album30": {"price": 5500, "name": "Coffeetable Album 30 pages"},
        "album20": {"price": 4000, "name": "Coffeetable Album 20 pages"},
        "album10": {"price": 3000, "name": "Coffeetable Album 10 pages"},
    }
    
    # For backward compatibility
    PHOTO_PACKAGES = {
        "basic": {"price": 3500, "hours": "4 hrs", "name": "Base Photographer (4 hrs)"},
        "standard": {"price": 7000, "hours": "4 hrs", "name": "Base Videographer (4 hrs shoot & edit)"},
        "premium": {"price": 8000, "hours": "whole day", "name": "PreNup & Save the Date Package"},
        "gold": {"price": 40000, "hours": "whole day", "name": "Wedding Gold - 2 Photo, 3 Video, 1 SDE"},
        "silver": {"price": 25000, "hours": "whole day", "name": "Wedding Silver - 1 Photo, 2 Video"},
        "bronze": {"price": 18000, "hours": "whole day", "name": "Wedding Bronze - 1 Photo, 1 Video"},
        "wedding": {"price": 25000, "hours": "whole day", "name": "Wedding Package (Silver/Gold/Bronze)"},
    }
    
    RESORT_ROOMS = {
        "standard": {"price": 2500, "capacity": 2, "name": "Standard Room"},
        "deluxe": {"price": 3500, "capacity": 3, "name": "Deluxe Room"},
        "family": {"price": 5000, "capacity": 5, "name": "Family Villa"},
        "barkada": {"price": 8000, "capacity": 10, "name": "Barkada Whole Resort"},
    }

    def get_page_token(self, page_id):
        if page_id and page_id in self.MULTI_PAGE_TOKENS:
            return self.MULTI_PAGE_TOKENS[page_id]
        return self.PAGE_TOKEN
    
    def get_business_config(self, page_id):
        if page_id and page_id in self.BUSINESS_CONFIGS:
            return self.BUSINESS_CONFIGS[page_id]
        return {
            "type": self.BUSINESS_TYPE,
            "name": self.BUSINESS_NAME,
            "hours": self.BUSINESS_HOURS,
            "location": self.LOCATION
        }
