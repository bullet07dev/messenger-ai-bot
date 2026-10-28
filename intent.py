import re

class IntentClassifier:
    # Enterprise intent classifier - 0ms, no AI needed, free
    # Classifies message into intent before calling LLM
    
    BOOKING_KEYWORDS = ["book", "booking", "reserve", "reservation", "magbook", "magpareserve", "agbook", "agpareserve", "wedding", "prenup", "birthday", "debut", "resort", "room", "villa"]
    HUMAN_KEYWORDS = ["human", "agent", "staff", "manager", "tawagan", "kailangan ko tao", "need human", "real person"]
    FAQ_KEYWORDS = ["rate", "rates", "price", "pricing", "magkano", "manu", "presyo", "package", "gold", "silver", "bronze", "standard", "deluxe", "album"]
    CANCEL_KEYWORDS = ["cancel", "kansela", "sardeng"]
    MY_BOOKINGS_KEYWORDS = ["my booking", "my bookings", "my order", "status", "booking status"]
    
    def classify(self, text, current_state=None):
        lower = text.lower().strip()
        
        # If already in booking flow, stay in booking
        if current_state and current_state.get("step"):
            return "BOOKING_FLOW"
        
        # Check payloads (quick replies)
        if "_" in text and text.isupper():
            if any(x in text for x in ["ROOM_", "GUESTS_", "WEDDING_", "EVENT_", "PKG_", "ALBUM_"]):
                return "BOOKING_FLOW"
        
        if any(k in lower for k in self.CANCEL_KEYWORDS):
            return "CANCEL"
        
        if any(k in lower for k in self.MY_BOOKINGS_KEYWORDS):
            return "MY_BOOKINGS"
        
        if any(k in lower for k in self.HUMAN_KEYWORDS):
            return "HUMAN_HANDOFF"
        
        if any(k in lower for k in self.BOOKING_KEYWORDS) or lower in ["book", "rates", "photo", "resort"]:
            # Distinguish BOOK intent vs FAQ
            if lower in ["book", "booking", "reserve"] or "book" in lower.split():
                return "BOOKING_START"
            if any(k in lower for k in self.FAQ_KEYWORDS) and "book" not in lower:
                return "FAQ"
            return "BOOKING_START"
        
        if any(k in lower for k in self.FAQ_KEYWORDS):
            return "FAQ"
        
        return "CHIT_CHAT"