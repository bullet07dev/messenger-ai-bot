import logging
logger = logging.getLogger(__name__)

# Enterprise RAG - Free tier using Qdrant or Supabase pgvector
# For now, implement local knowledge base that will be replaced by vector DB later

KNOWLEDGE_BASE = '''
Business: Jeafred Photography & Resort, Guimba, Nueva Ecija

PHOTOGRAPHY RATES:
- Base Photographer 4hrs: ₱3,500 (Referral ₱1k)
- Videographer 4hrs: ₱7,000 (Referral ₱1k)
- SDE Editor whole day: ₱6,500 (Referral ₱500)
- Drone Pilot whole day: ₱5,000 (Referral ₱500)
- PreNup & Save the Date: ₱8,000 (Referral ₱500)
- Wedding Gold: ₱40,000 (2 Photo, 3 Video, 1 SDE, Referral ₱2k) Includes: Prenup unli enhanced, Save the Date Video 2-5min with aerials, Wedding Photo unli, Video Full Doc with aerials, Same Day Edit
- Wedding Silver: ₱25,000 (1 Photo, 2 Video, Referral ₱1.5k)
- Wedding Bronze: ₱18,000 (1 Photo, 1 Video, Referral ₱1k)
- Album 30 pages: ₱5,500
- Album 20 pages: ₱4,000
- Album 10 pages: ₱3,000

RESORT RATES:
- Standard Room 2 pax: ₱2,500/night
- Deluxe Room 3 pax: ₱3,500/night
- Family Villa 5 pax: ₱5,000/night
- Barkada Package 10 pax: ₱8,000/night

LANGUAGES: Ilocano (local Guimba), Tagalog, English. Detect and reply in same language.

BOOKING FLOW: Customer says BOOK -> ask details -> confirm.

POLICIES: Downpayment 50% to confirm booking. Cancellation 1 week before = 50% refund. No show = no refund.
'''

class RAGService:
    def __init__(self, config):
        self.config = config
        self.qdrant_client = None
        if config.QDRANT_URL and config.QDRANT_API_KEY:
            try:
                from qdrant_client import QdrantClient
                self.qdrant_client = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)
                logger.info("Qdrant connected")
            except Exception as e:
                logger.error(f"Qdrant connection failed: {e}")
    
    def search(self, query):
        # Simple keyword search for now - will be replaced by vector search
        # When Qdrant is enabled, this will do semantic search
        query_lower = query.lower()
        relevant = []
        
        # Simple logic - if query contains rate keywords, return rates
        if any(k in query_lower for k in ["rate", "price", "magkano", "manu", "presyo", "gold", "silver", "bronze", "standard", "deluxe", "family", "barkada", "photo", "video", "drone", "sde", "album"]):
            return KNOWLEDGE_BASE
        
        if self.qdrant_client:
            try:
                # Future: semantic search
                # results = self.qdrant_client.search(collection_name="knowledge", query_vector=...)
                pass
            except:
                pass
        
        return KNOWLEDGE_BASE if relevant or len(query) > 3 else ""
    
    def get_context_for_llm(self, query):
        context = self.search(query)
        if context:
            return f"Business Knowledge:\n{context}\n\nUse this to answer accurately. Don't hallucinate prices."
        return ""