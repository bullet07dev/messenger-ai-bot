import requests, logging
from ..config import Config
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.config = Config()
    
    def detect_language(self, text):
        lower = text.lower()
        
        # Ilocano keywords (Guimba, Nueva Ecija)
        ilocano_keywords = [
            "madi", "syak", "sika", "datayo", "dakami", "ania", "anya", "manu", "kasano", "sadino", "kaano",
            "kay", "man", "met", "nga", "daytoy", "dayta", "kasta", "awan", "adda", "nalaing", "napintas",
            "manong", "manang", "ading", "apo", "kabsat", "gayyem"
        ]
        
        # Tagalog keywords
        tagalog_keywords = [
            "magkano", "saan", "kailan", "paano", "ano", "sino", "bakit",
            "po", "opo", "ako", "ikaw", "kami", "kayo", "sila",
            "gusto", "kailangan", "puwede", "pwede", "pabili", "magbook",
            "salamat", "kumusta", "kasal", "binyag", "kuha", "lang po", "na po"
        ]
        
        ilocano_score = sum(1 for k in ilocano_keywords if k in lower)
        tagalog_score = sum(1 for k in tagalog_keywords if k in lower)
        
        if ilocano_score >= 1 and ("madi" in lower or "syak" in lower or "man met" in lower or "ania" in lower or "anya" in lower):
            return "ilocano"
        elif tagalog_score >= 1:
            return "tagalog"
        else:
            return "english"
    
    def ask_gemini(self, msg, name="boss", biz=None):
        if not self.config.GEMINI_KEY:
            return None
        biz = biz or {}
        lang = self.detect_language(msg)
        
        if lang == "ilocano":
            lang_instruction = "Reply in Ilocano mixed with Taglish (use 'manong/manang' respect, Ilocano is spoken in Guimba). Use Ilocano words like madi, syak man met, anya, manu, kasano, etc."
        elif lang == "tagalog":
            lang_instruction = "Reply in Tagalog (Taglish okay, use po/opo for respect)"
        else:
            lang_instruction = "Reply in English (Taglish okay if needed)"
        
        for model in self.config.GEMINI_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.config.GEMINI_KEY}"
                prompt = f"""You are {biz.get('name', 'Jeafred Photography')} assistant from Guimba, Nueva Ecija. You speak 3 languages fluently: Ilocano (local), Tagalog, English.
Business type: {biz.get('type', 'photographer')}
Real rates: Base Photo 4hrs 3500 (referral 1k), Video 4hrs 7000 (referral 1k), SDE whole day 6500 (referral 500), Drone whole day 5000 (referral 500), PreNup 8k (referral 500), Wedding Gold 40k (2P 3V 1SDE referral 2k), Silver 25k (1P 2V referral 1.5k), Bronze 18k (1P 1V referral 1k), Album 30p 5500 20p 4000 10p 3000.

Detected customer language: {lang}
Instruction: {lang_instruction}

Rules:
- If customer speaks Ilocano, reply in Ilocano + Taglish mix (Guimba style)
- If Tagalog, reply Tagalog with po/opo
- If English, reply English
- Be friendly, respectful, short 2-3 sentences
- If booking, say Type BOOK / Type BOOK para mag-book / Type BOOK tapno ag-book (Ilocano)

Customer {name} says: {msg}
Reply in {lang}:"""
                r = requests.post(url, headers={"Content-Type": "application/json"}, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": 350, "temperature": 0.7}}, timeout=12)
                data = r.json()
                if 'candidates' in data and data['candidates']:
                    return data['candidates'][0]['content']['parts'][0]['text'].strip()
            except:
                continue
        return None
    
    def ask_groq(self, msg, name="boss", biz=None):
        if not self.config.GROQ_KEY:
            return None
        biz = biz or {}
        lang = self.detect_language(msg)
        
        if lang == "ilocano":
            lang_instruction = "Reply in Ilocano + Taglish (Guimba style, use manong/manang, madi, syak man met)"
        elif lang == "tagalog":
            lang_instruction = "Reply in Tagalog with po/opo"
        else:
            lang_instruction = "Reply in English"
        
        for model in self.config.GROQ_MODELS:
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {self.config.GROQ_KEY}", "Content-Type": "application/json"}, json={"model": model, "messages": [{"role": "system", "content": f"You are {biz.get('name')} assistant from Guimba. You speak Ilocano, Tagalog, English. {lang_instruction}. Rates: Photo 3500 Video 7000 SDE 6500 Drone 5000 PreNup 8000 Gold 40k Silver 25k Bronze 18k Album 30p 5500 20p 4000 10p 3000. Be friendly."}, {"role": "user", "content": msg}], "temperature": 0.7, "max_tokens": 350}, timeout=12)
                data = r.json()
                if 'choices' in data:
                    return data['choices'][0]['message']['content'].strip()
            except:
                continue
        return None
    
    def ask_rule(self, msg, name="boss", biz=None):
        biz = biz or {}
        lang = self.detect_language(msg)
        m = msg.lower()
        
        # ILOCANO responses
        if lang == "ilocano":
            if any(x in m for x in ["hi", "hello", "hey", "kumusta", "madi", "syak", "anya"]):
                return f"Naimbag nga aldaw, {name}! Syak man met! Welcome iti {biz.get('name', 'Jeafred Photography')}! 📸\n\nWedding Packages:\n🥇 Gold 40k (2P 3V 1SDE)\n🥈 Silver 25k (1P 2V)\n🥉 Bronze 18k (1P 1V)\n\nBase: Photo 4hrs 3.5k, Video 4hrs 7k, Drone 5k, SDE 6.5k, PreNup 8k\n\nType BOOK tapno ag-book! Type RATES para rates. Madi met! 😊"
            
            if "rates" in m or "magkano" in m or "manu" in m or "presyo" in m or "package" in m:
                return f"""📸 {biz.get('name', 'Jeafred Photography')} Rates, {name}:

Base Rates (4hrs):
📸 Photographer - ₱3,500 (Referral ₱1k)
🎥 Videographer - ₱7,000 (Referral ₱1k)
✂️ SDE Editor whole day - ₱6,500 (Referral ₱500)
🚁 Drone Pilot whole day - ₱5,000 (Referral ₱500)
💍 PreNup & Save the Date - ₱8,000 (Referral ₱500)

Wedding Packages:
🥇 GOLD - ₱40k (Referral ₱2k) 2 Photo, 3 Video, 1 SDE
Kasama na: Prenup unli enhanced, Save the Date Video 2-5min with aerials, Wedding Photo unli, Video Full Doc with aerials, Same Day Edit

🥈 SILVER - ₱25k (Referral ₱1.5k) 1 Photo, 2 Video
🥉 BRONZE - ₱18k (Referral ₱1k) 1 Photo, 1 Video

Add-ons:
📚 Album 30 pages - ₱5,500
📚 Album 20 pages - ₱4,000
📚 Album 10 pages - ₱3,000

Type BOOK tapno ag-book, {name}! Syak man met!
"""
            if "salamat" in m or "thank" in m or "madi" in m:
                return f"Awan aniaman, {name}! Syak man met! 😊 Type BOOK tapno ag-book manen."
            
            return f"Salamat iti message mo, {name}! Kunam '{msg}'. Para ag-book iti {biz.get('name')}, type BOOK lang. Para rates, type RATES. Madi met! Syak man met!"
        
        # TAGALOG responses
        elif lang == "tagalog":
            if any(x in m for x in ["hi", "hello", "hey", "kumusta", "musta"]):
                return f"Kumusta po {name}! Welcome po sa {biz.get('name', 'Jeafred Photography')}! 📸\n\nWedding Packages po:\n🥇 Gold 40k (2P 3V 1SDE)\n🥈 Silver 25k (1P 2V)\n🥉 Bronze 18k (1P 1V)\n\nBase: Photo 4hrs 3.5k, Video 4hrs 7k, Drone 5k, SDE 6.5k, PreNup 8k\n\nType BOOK po para mag-book! Type RATES para rates. Syak man met! 😊"
            
            if "rates" in m or "magkano" in m or "presyo" in m or "package" in m:
                return f"""📸 {biz.get('name', 'Jeafred Photography')} Rates po, {name}:

Base Rates (4hrs) po:
📸 Photographer - ₱3,500 (Referral ₱1k)
🎥 Videographer - ₱7,000 (Referral ₱1k)
✂️ SDE Editor whole day - ₱6,500 (Referral ₱500)
🚁 Drone Pilot whole day - ₱5,000 (Referral ₱500)
💍 PreNup & Save the Date - ₱8,000 (Referral ₱500)

Wedding Packages po:
🥇 GOLD - ₱40k (Referral ₱2k)
🥈 SILVER - ₱25k (Referral ₱1.5k)
🥉 BRONZE - ₱18k (Referral ₱1k)

Add-ons po: Album 30p ₱5.5k, 20p ₱4k, 10p ₱3k

Type BOOK po para mag-book, {name}! Salamat po!
"""
            return f"Salamat po sa message, {name}! Sabi nyo po '{msg}'. Para mag-book po sa {biz.get('name')}, type BOOK lang po. Para rates, type RATES po."
        
        # ENGLISH
        else:
            if any(x in m for x in ["hi", "hello", "hey"]):
                return f"Hi {name}! Welcome to {biz.get('name', 'Jeafred Photography')}! 📸\n\nWedding Packages:\n🥇 Gold 40k (2P 3V 1SDE)\n🥈 Silver 25k (1P 2V)\n🥉 Bronze 18k (1P 1V)\n\nBase: Photo 4hrs 3.5k, Video 4hrs 7k, Drone 5k, SDE 6.5k, PreNup 8k\n\nType BOOK to book! Type RATES for rates."
            
            if "rates" in m or "price" in m or "package" in m:
                return f"""📸 {biz.get('name', 'Jeafred Photography')} Rates:

Base Rates (4hrs):
📸 Photographer - ₱3,500 (Referral ₱1k)
🎥 Videographer - ₱7,000 (Referral ₱1k)
✂️ SDE Editor whole day - ₱6,500 (Referral ₱500)
🚁 Drone Pilot whole day - ₱5,000 (Referral ₱500)
💍 PreNup & Save the Date - ₱8,000 (Referral ₱500)

Wedding Packages:
🥇 GOLD - ₱40k (Referral ₱2k) 2 Photo, 3 Video, 1 SDE
🥈 SILVER - ₱25k (Referral ₱1.5k) 1 Photo, 2 Video
🥉 BRONZE - ₱18k (Referral ₱1k) 1 Photo, 1 Video

Add-ons: Album 30p ₱5.5k, 20p ₱4k, 10p ₱3k

Type BOOK to book, {name}!
"""
            return f"Thanks {name}! You said '{msg}'. Type BOOK to book photography, or RATES to see packages. Hours: {biz.get('hours')}"
    
    def get_reply(self, msg, name="boss", biz=None):
        for fn in [self.ask_gemini, self.ask_groq]:
            try:
                r = fn(msg, name, biz)
                if r:
                    return r
            except:
                continue
        return self.ask_rule(msg, name, biz)
