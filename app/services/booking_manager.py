import uuid, json, os, logging
from datetime import datetime
logger = logging.getLogger(__name__)
BOOKING_FILE = "/tmp/bookings.json"
bookings = {}
user_states = {}

def load_bookings():
    try:
        if os.path.exists(BOOKING_FILE):
            with open(BOOKING_FILE, 'r') as f:
                bookings.update(json.load(f))
    except: pass
def save_bookings():
    try:
        with open(BOOKING_FILE, 'w') as f:
            json.dump(bookings, f, indent=2)
    except: pass
load_bookings()

class BookingManager:
    def detect_lang(self, text):
        lower = text.lower()
        ilocano = ["madi", "syak", "ania", "anya", "manu", "man met", "kabsat", "manong", "manang"]
        if any(k in lower for k in ilocano):
            return "ilocano"
        tagalog = ["po", "opo", "magkano", "saan", "salamat", "kumusta"]
        if any(k in lower for k in tagalog):
            return "tagalog"
        return "english"
    
    def is_tagalog(self, text):
        return self.detect_lang(text) in ["tagalog", "ilocano"]

        tl = ["magkano", "po", "opo", "saan", "kailan", "gusto", "salamat", "kumusta", "madi", "syak", "kasal", "binyag", "pabili", "magbook"]
        return any(k in text.lower() for k in tl)

    def get_state(self, uid):
        return user_states.get(uid, {"flow": None, "step": None, "data": {}})
    def set_state(self, uid, flow, step, data):
        user_states[uid] = {"flow": flow, "step": step, "data": data}
    def clear_state(self, uid):
        user_states.pop(uid, None)
    
    def handle(self, uid, text, customer_name, biz_config, config):
        state = self.get_state(uid)
        flow = state["flow"]
        step = state["step"]
        data = state["data"]
        lower = text.lower().strip()
        
        if flow is None:
            btype = biz_config.get("type", "photographer").lower()
            if btype == "resort":
                return self._start_resort(uid, customer_name, biz_config)
            elif btype in ["product", "shop"]:
                return self._start_product(uid, customer_name, biz_config)
            elif btype in ["photographer", "photo", "photography", "multi"]:
                # For photographer business, go directly to photo flow but detect resort/product keywords
                if any(k in lower for k in ["resort", "room", "villa"]):
                    return self._start_resort(uid, customer_name, biz_config)
                elif any(k in lower for k in ["buy", "order", "product", "shop"]):
                    return self._start_product(uid, customer_name, biz_config)
                else:
                    return self._start_photo(uid, customer_name, biz_config)

        if flow == "choose":
            if "resort" in lower:
                return self._start_resort(uid, customer_name, biz_config)
            elif "photo" in lower:
                return self._start_photo(uid, customer_name, biz_config)
            elif "product" in lower:
                return self._start_product(uid, customer_name, biz_config)

        if flow == "resort":
            return self._handle_resort(uid, text, customer_name, biz_config, config)
        if flow == "photographer":
            return self._handle_photo(uid, text, customer_name, biz_config, config)
        if flow == "product":
            return self._handle_product(uid, text, customer_name, biz_config, config)

    # RESORT (simple)
    def _start_resort(self, uid, customer_name, biz):
        self.set_state(uid, "resort", "checkin", {})
        return f"🏖️ Resort Booking at {biz.get('name')}! (Tagalog/English OK)\n\n\nRooms:\n🏠 Standard 2pax ₱2,500\n✨ Deluxe 3pax ₱3,500\n👨‍👩‍👧 Family 5pax ₱5,000\n🎉 Barkada 10pax ₱8,000\n\nWhen is check-in? (e.g., Dec 25)"
    def _handle_resort(self, uid, text, customer_name, biz, config):
        state = self.get_state(uid)
        step, data = state["step"], state["data"]
        if step == "checkin":
            data["checkin"] = text
            self.set_state(uid, "resort", "checkout", data)
            return f"Check-in: {text} 📅\nCheck-out?"
        if step == "checkout":
            data["checkout"] = text
            self.set_state(uid, "resort", "guests", data)
            return "How many guests?"
        if step == "guests":
            data["guests"] = text
            self.set_state(uid, "resort", "room_type", data)
            return "Room type? STANDARD, DELUXE, FAMILY, BARKADA"
        if step == "room_type":
            rt = text.lower()
            for k in config.RESORT_ROOMS:
                if k in rt:
                    rt = k
                    break
            if rt not in config.RESORT_ROOMS:
                return "Choose: STANDARD, DELUXE, FAMILY, BARKADA"
            data["room_type"] = rt
            data["price"] = config.RESORT_ROOMS[rt]["price"]
            self.set_state(uid, "resort", "name", data)
            return f"{config.RESORT_ROOMS[rt]['name']} ₱{data['price']}/night\nYour full name?"
        if step == "name":
            data["name"] = text
            self.set_state(uid, "resort", "phone", data)
            return "Phone number?"
        if step == "phone":
            data["phone"] = text
            bid = f"RESORT-{str(uuid.uuid4())[:8].upper()}"
            data.update({"booking_id": bid, "type": "resort", "business": biz.get('name'), "created_at": datetime.now().isoformat(), "status": "pending", "user_id": uid})
            bookings[bid] = data
            save_bookings()
            self.clear_state(uid)
            return f"✅ Resort Booking! 📋 {bid}\n{biz.get('name')}\n{data['name']} 📱 {data['phone']}\n📅 {data['checkin']} to {data['checkout']} 👥 {data['guests']} 🏠 {data['room_type']} ₱{data['price']}\nStaff will confirm. Type BOOKING {bid}"

    # PHOTO - CUSTOM WITH YOUR REAL RATES
    def _start_photo(self, uid, customer_name, biz):
        self.set_state(uid, "photographer", "event_type", {})
        return f"""📸 Photography Booking at {biz.get('name', 'Jeafred Photography')}, {customer_name}!

What event do you need?

1️⃣ WEDDING - Gold 40k / Silver 25k / Bronze 18k
2️⃣ PRENUP - PreNup & Save the Date 8k (whole day)
3️⃣ BIRTHDAY / DEBUT / GRADUATION / FAMILY / BAPTISM / CORPORATE
   - Base Photo 4hrs - ₱3,500
   - Base Video 4hrs - ₱7,000
   - SDE Editor whole day - ₱6,500
   - Drone Pilot whole day - ₱5,000

Type: WEDDING, PRENUP, BIRTHDAY, DEBUT, etc.
Example: WEDDING"""

    def _handle_photo(self, uid, text, customer_name, biz, config):
        state = self.get_state(uid)
        step, data = state["step"], state["data"]
        lower = text.lower()
        
        if step == "event_type":
            data["event_type"] = text.upper()
            # If wedding, ask which package
            if "wedding" in lower:
                self.set_state(uid, "photographer", "wedding_package", data)
                return f"""Wedding noted! 💍 Choose package:

🥇 GOLD - ₱40,000 (Referral ₱2k)
Team: 2 Photographers, 3 Videographers, 1 SDE Editor
Includes: Prenup unli enhanced, Save the Date Video 2-5min with aerials, Wedding Photo unli enhanced, Wedding Video Full Doc with aerials, Same Day Edit

🥈 SILVER - ₱25,000 (Referral ₱1.5k)
Team: 1 Photographer, 2 Videographers
Includes: Prenup unli enhanced + RAW, Save the Date with aerials, Photo unli enhanced, Video Complete Highlights with aerials

🥉 BRONZE - ₱18,000 (Referral ₱1k)
Team: 1 Photographer, 1 Videographer
Includes: Prenup unli + RAW, Save the Date Video 2-5min, Photo unli enhanced, Video Highlights

Type GOLD, SILVER, or BRONZE"""
            else:
                # Non-wedding: ask if base rates or prenup
                if "prenup" in lower or "save the date" in lower:
                    data["service_type"] = "prenup"
                    data["price"] = 8000
                    data["package"] = "PreNup & Save the Date"
                self.set_state(uid, "photographer", "date", data)
                return f"{text} noted! 📸 When is event date? (e.g., Dec 30, 2026)"

        if step == "wedding_package":
            pkg = lower
            if "gold" in pkg:
                pkg = "gold"
            elif "silver" in pkg:
                pkg = "silver"
            elif "bronze" in pkg:
                pkg = "bronze"
            else:
                return "Please choose: GOLD, SILVER, or BRONZE"
            data["wedding_package"] = pkg
            data["price"] = config.WEDDING_PACKAGES[pkg]["price"]
            data["package"] = config.WEDDING_PACKAGES[pkg]["name"]
            data["team"] = config.WEDDING_PACKAGES[pkg]["team"]
            self.set_state(uid, "photographer", "date", data)
            return f"Great! {config.WEDDING_PACKAGES[pkg]['name']} - ₱{data['price']}\nWhen is wedding date?"

        if step == "date":
            data["date"] = text
            self.set_state(uid, "photographer", "time", data)
            return f"Date: {text}\nWhat time? (e.g., 2PM, 8AM)"
        if step == "time":
            data["time"] = text
            self.set_state(uid, "photographer", "location", data)
            return f"Time: {text}\nVenue/location? (e.g., Guimba Church + Reception)"
        if step == "location":
            data["location"] = text
            # If not wedding and not prenup, ask service type
            if "wedding_package" not in data and "service_type" not in data:
                self.set_state(uid, "photographer", "service", data)
                return f"""Location: {text}

What service do you need?

📸 Base Photographer 4hrs - ₱3,500 (Referral ₱1k)
🎥 Base Videographer 4hrs - ₱7,000 (Referral ₱1k)
✂️ SDE Editor whole day - ₱6,500 (Referral ₱500)
🚁 Drone Pilot whole day - ₱5,000 (Referral ₱500)

You can also combine! Example: Type PHOTOGRAPHER + VIDEOGRAPHER or just PHOTOGRAPHER

Add-ons:
📚 Album 30 pages - ₱5,500
📚 Album 20 pages - ₱4,000
📚 Album 10 pages - ₱3,000

What do you need?"""
            else:
                self.set_state(uid, "photographer", "addon", data)
                return f"""Location: {text}

Add-on? (Optional)
📚 Album 30 pages - ₱5,500
📚 Album 20 pages - ₱4,000
📚 Album 10 pages - ₱3,000
Type ALBUM30, ALBUM20, ALBUM10, or NONE"""

        if step == "service":
            data["service_type"] = text
            # Try to parse price
            price = 0
            lower_s = text.lower()
            if "photographer" in lower_s and "videographer" in lower_s:
                price = 3500 + 7000  # 10.5k
            elif "photographer" in lower_s:
                price = 3500
            elif "videographer" in lower_s or "video" in lower_s:
                price = 7000
            elif "drone" in lower_s:
                price = 5000
            elif "sde" in lower_s or "editor" in lower_s:
                price = 6500
            data["price"] = price if price else 3500
            data["package"] = text
            self.set_state(uid, "photographer", "addon", data)
            return f"""Service: {text} - ₱{data['price']}

Add-on Album? (Optional)
📚 Album 30 pages - ₱5,500
📚 Album 20 pages - ₱4,000
📚 Album 10 pages - ₱3,000
Type ALBUM30, ALBUM20, ALBUM10, or NONE"""

        if step == "addon":
            if "album" in lower:
                data["addon"] = text.upper()
                # Add price
                if "30" in text:
                    data["addon_price"] = 5500
                elif "20" in text:
                    data["addon_price"] = 4000
                elif "10" in text:
                    data["addon_price"] = 3000
            else:
                data["addon"] = "None"
                data["addon_price"] = 0
            self.set_state(uid, "photographer", "name", data)
            return f"Add-on: {data['addon']}\nYour full name?"
        if step == "name":
            data["name"] = text
            self.set_state(uid, "photographer", "phone", data)
            return f"Thanks {text}! Phone number?"
        if step == "phone":
            data["phone"] = text
            bid = f"PHOTO-{str(uuid.uuid4())[:8].upper()}"
            total = data.get("price", 0) + data.get("addon_price", 0)
            data.update({"booking_id": bid, "type": "photographer", "business": biz.get('name'), "created_at": datetime.now().isoformat(), "status": "pending", "user_id": uid, "total": total})
            bookings[bid] = data
            save_bookings()
            self.clear_state(uid)
            
            # Build detailed confirmation
            addon_str = f"\n📚 Add-on: {data.get('addon')} ₱{data.get('addon_price')}" if data.get('addon_price', 0) > 0 else ""
            team_str = f"\n👥 Team: {data.get('team')}" if data.get('team') else ""
            
            return f"""✅ Photography Booking Received!

📋 ID: {bid}
📸 {biz.get('name')}
👤 {data['name']} 📱 {data['phone']}
🎉 Event: {data.get('event_type')}
📦 Package: {data.get('package')} - ₱{data.get('price')}{team_str}
{addon_str}
📅 Date: {data.get('date')} at {data.get('time')}
📍 Venue: {data.get('location')}
💰 Total: ₱{total}

Staff will confirm within 1 hour (Hours: {biz.get('hours', '8AM-10PM')}).

Add-ons available: Coffeetable Album 30p ₱5.5k, 20p ₱4k, 10p ₱3k

Type BOOKING {bid} to check status.

Salamat, {customer_name}! Syak man met! 🙏"""

    # PRODUCT
    def _start_product(self, uid, customer_name, biz):
        self.set_state(uid, "product", "product", {})
        return f"🛒 Order at {biz.get('name')}! What product do you want to buy?"
    def _handle_product(self, uid, text, customer_name, biz, config):
        state = self.get_state(uid)
        step, data = state["step"], state["data"]
        if step == "product":
            data["product"] = text
            self.set_state(uid, "product", "quantity", data)
            return f"{text} noted! How many?"
        if step == "quantity":
            data["quantity"] = text
            self.set_state(uid, "product", "address", data)
            return "Delivery address?"
        if step == "address":
            data["address"] = text
            self.set_state(uid, "product", "name", data)
            return "Full name?"
        if step == "name":
            data["name"] = text
            self.set_state(uid, "product", "phone", data)
            return "Phone number?"
        if step == "phone":
            data["phone"] = text
            bid = f"ORDER-{str(uuid.uuid4())[:8].upper()}"
            data.update({"booking_id": bid, "type": "product", "business": biz.get('name'), "created_at": datetime.now().isoformat(), "status": "pending", "user_id": uid})
            bookings[bid] = data
            save_bookings()
            self.clear_state(uid)
            return f"✅ Order! 📋 {bid}\n{data['product']} x {data['quantity']}\n📍 {data['address']}\n👤 {data['name']} 📱 {data['phone']}\nStaff will confirm. BOOKING {bid}"

    def get_booking(self, bid):
        return bookings.get(bid.upper())
    def list_user_bookings(self, uid):
        return [b for b in bookings.values() if b.get("user_id") == uid]
