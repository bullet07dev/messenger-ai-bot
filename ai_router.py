import requests, logging, time
from .rag import RAGService
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, config):
        self.config = config
        self.rag = RAGService(config)
        self.last_model_used = "none"
    
    def detect_language(self, text, user_lang_pref=None):
        lower = text.lower()
        # Ilocano - Guimba dialect
        ilocano_keywords = ["madi", "syak", "sika", "ania", "anya", "manu", "kasano", "sadino", "kaano", "man met", "kabsat", "manong", "manang", "adda", "awan", "ag-", "intong bigat", "syak man met"]
        tagalog_keywords = ["magkano", "saan", "kailan", "paano", "ano", "sino", "bakit", "po", "opo", "ako", "ikaw", "kami", "gusto", "kailangan", "puwede", "salamat", "kumusta"]
        
        ilo_score = sum(1 for k in ilocano_keywords if k in lower)
        tag_score = sum(1 for k in tagalog_keywords if k in lower)
        
        # If user previously spoke Ilocano, prefer Ilocano
        if user_lang_pref == "ilocano":
            if tag_score == 0 or ilo_score > 0:
                return "ilocano"
        if user_lang_pref == "tagalog":
            if ilo_score == 0 or tag_score > 0:
                return "tagalog"
        
        if ilo_score >= 1 and ("madi" in lower or "syak" in lower or "man met" in lower or "ania" in lower or "anya" in lower or "intong" in lower):
            return "ilocano"
        elif tag_score >= 1:
            return "tagalog"
        else:
            return "english"
    
    def ask_gemini(self, msg, name, biz, lang, context=""):
        if not self.config.GEMINI_KEY or not self.config.GEMINI_KEY.startswith("AIza"):
            if self.config.GEMINI_KEY:
                logger.warning(f"GEMINI_KEY invalid format: starts with {self.config.GEMINI_KEY[:3]}... must start with AIza")
            return None
        
        if lang == "ilocano":
            lang_instruction = "Reply in Ilocano mixed with Taglish (Guimba, Nueva Ecija style, respectful manong/manang, use words like madi, syak man met, anya, manu, kasano, kabsat)"
        elif lang == "tagalog":
            lang_instruction = "Reply in Tagalog (Taglish okay, use po/opo for respect)"
        else:
            lang_instruction = "Reply in English (Taglish okay)"
        
        biz_name = biz.get('name', 'Jeafred Photography & Resort')
        biz_type = biz.get('type', 'multi')
        
        prompt = f'''You are {biz_name} assistant from Guimba, Nueva Ecija. Business type: {biz_type}
{context}

Customer: {name}, Language: {lang}, Instruction: {lang_instruction}
Customer says: {msg}

Rules:
- Be friendly, short 2-3 sentences, respectful
- Use knowledge base for rates, don't hallucinate
- If booking intent, say Type BOOK / Type BOOK po / Type BOOK tapno ag-book (based on language)
- Detect language and reply in same language
- Business hours: {biz.get('hours', '8AM-10PM')}

Reply in {lang}:'''
        
        for model in self.config.GEMINI_MODELS:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.config.GEMINI_KEY}"
                r = requests.post(url, headers={"Content-Type": "application/json"}, 
                                  json={"contents": [{"parts": [{"text": prompt}]}], 
                                        "generationConfig": {"maxOutputTokens": 400, "temperature": 0.7}}, 
                                  timeout=15)
                data = r.json()
                if 'candidates' in data and data['candidates']:
                    text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                    self.last_model_used = f"gemini-{model}"
                    logger.info(f"Gemini success: {model}")
                    return text
                else:
                    logger.warning(f"Gemini {model} no candidates: {str(data)[:300]}")
            except Exception as e:
                logger.warning(f"Gemini {model} error: {e}")
                continue
        return None
    
    def ask_groq(self, msg, name, biz, lang, context=""):
        if not self.config.GROQ_KEY or not self.config.GROQ_KEY.startswith("gsk_"):
            return None
        
        if lang == "ilocano":
            lang_instruction = "Reply in Ilocano + Taglish (Guimba style, manong/manang, madi, syak man met)"
        elif lang == "tagalog":
            lang_instruction = "Reply in Tagalog with po/opo"
        else:
            lang_instruction = "Reply in English"
        
        biz_name = biz.get('name', 'Jeafred Photography & Resort')
        system_prompt = f"You are {biz_name} assistant from Guimba. {lang_instruction}. {context} Be friendly, short 2-3 sentences. If booking, say Type BOOK. Hours: {biz.get('hours', '8AM-10PM')}"
        
        for model in self.config.GROQ_MODELS:
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                  headers={"Authorization": f"Bearer {self.config.GROQ_KEY}", "Content-Type": "application/json"},
                                  json={"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": msg}], "temperature": 0.7, "max_tokens": 400},
                                  timeout=15)
                data = r.json()
                if 'choices' in data:
                    text = data['choices'][0]['message']['content'].strip()
                    self.last_model_used = f"groq-{model}"
                    logger.info(f"Groq success: {model}")
                    return text
                else:
                    logger.warning(f"Groq {model} no choices: {str(data)[:300]}")
            except Exception as e:
                logger.warning(f"Groq {model} error: {e}")
                continue
        return None
    
    def ask_rule(self, msg, name, biz, lang):
        # Fallback - rule based, trilingual
        m = msg.lower()
        biz_name = biz.get('name', 'Jeafred Photography')
        
        if lang == "ilocano":
            if any(x in m for x in ["hi", "hello", "kumusta", "madi", "syak", "anya", "ania"]):
                return f"Naimbag nga aldaw, {name}! Syak man met! Welcome iti {biz_name}! 📸\n\nWedding: Gold 40k, Silver 25k, Bronze 18k\nBase: Photo 3.5k, Video 7k, Drone 5k, SDE 6.5k, PreNup 8k\nResort: Standard 2.5k, Deluxe 3.5k, Family 5k, Barkada 8k\n\nType BOOK tapno ag-book! Type RATES para rates. Madi met! 😊"
            if any(x in m for x in ["rates", "magkano", "manu", "presyo", "package"]):
                return f"📸 {biz_name} Rates, {name}:\nPhoto 3.5k, Video 7k, SDE 6.5k, Drone 5k, PreNup 8k\nGold 40k (2P 3V 1SDE), Silver 25k (1P 2V), Bronze 18k (1P 1V)\nAlbum 30p 5.5k 20p 4k 10p 3k\nResort: Standard 2.5k Deluxe 3.5k Family 5k Barkada 8k\nType BOOK tapno ag-book! Syak man met!"
            return f"Salamat iti message mo, {name}! Kunam '{msg}'. Para ag-book iti {biz_name}, type BOOK lang. Para rates, type RATES. Madi met! Syak man met!"
        
        elif lang == "tagalog":
            if any(x in m for x in ["hi", "hello", "kumusta"]):
                return f"Kumusta po {name}! Welcome po sa {biz_name}! 📸\n\nWedding po: Gold 40k, Silver 25k, Bronze 18k\nBase: Photo 3.5k, Video 7k, Drone 5k, SDE 6.5k, PreNup 8k\nResort: Standard 2.5k, Deluxe 3.5k, Family 5k, Barkada 8k\n\nType BOOK po para mag-book! Type RATES para rates. Syak man met! 😊"
            if any(x in m for x in ["rates", "magkano", "presyo"]):
                return f"📸 {biz_name} Rates po, {name}:\nPhoto 3.5k, Video 7k, SDE 6.5k, Drone 5k, PreNup 8k\nGold 40k, Silver 25k, Bronze 18k\nAlbum 30p 5.5k 20p 4k 10p 3k\nResort: Standard 2.5k Deluxe 3.5k Family 5k Barkada 8k\nType BOOK po para mag-book! Syak man met! 🙏"
            return f"Salamat po sa message nyo, {name}! Sabi nyo '{msg}'. Para mag-book sa {biz_name}, type BOOK lang po. Para rates, type RATES po. Syak man met! 😊"
        
        else:
            if any(x in m for x in ["hi", "hello", "hey"]):
                return f"Hi {name}! Welcome to {biz_name}! 📸\n\nWedding: Gold 40k, Silver 25k, Bronze 18k\nBase: Photo 3.5k, Video 7k, Drone 5k, SDE 6.5k, PreNup 8k\nResort: Standard 2.5k, Deluxe 3.5k, Family 5k, Barkada 8k\n\nType BOOK to book! Type RATES for rates. 😊"
            if any(x in m for x in ["rates", "price", "package"]):
                return f"📸 {biz_name} Rates, {name}:\nPhoto 3.5k, Video 7k, SDE 6.5k, Drone 5k, PreNup 8k\nGold 40k (2P 3V 1SDE), Silver 25k (1P 2V), Bronze 18k (1P 1V)\nAlbum 30p 5.5k 20p 4k 10p 3k\nResort: Standard 2.5k Deluxe 3.5k Family 5k Barkada 8k\nType BOOK to book!"
            return f"Thanks for your message, {name}! You said '{msg}'. To book at {biz_name}, type BOOK. For rates, type RATES. 😊"
    
    def get_reply(self, msg, name, biz, user_lang_pref=None):
        lang = self.detect_language(msg, user_lang_pref)
        context = self.rag.get_context_for_llm(msg)
        
        # Try Gemini first, then Groq, then rule-based (enterprise router)
        reply = None
        
        # Try Gemini
        reply = self.ask_gemini(msg, name, biz, lang, context)
        if reply:
            return reply, lang, self.last_model_used
        
        # Try Groq
        reply = self.ask_groq(msg, name, biz, lang, context)
        if reply:
            return reply, lang, self.last_model_used
        
        # Fallback rule-based
        reply = self.ask_rule(msg, name, biz, lang)
        self.last_model_used = "rule-based"
        return reply, lang, self.last_model_used