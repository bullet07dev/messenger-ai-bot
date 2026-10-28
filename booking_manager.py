import uuid, json, os, logging, re
from datetime import datetime
logger = logging.getLogger(__name__)

# Enterprise booking manager with Supabase support + in-memory fallback
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
    def __init__(self, supabase_service=None):
        self.supabase = supabase_service
    
    def get_state(self, uid):
        # Try Supabase first, fallback to memory
        if self.supabase:
            state = self.supabase.get_state(uid)
            if state:
                return state
        return user_states.get(uid, {"flow": None, "step": None, "data": {}, "history": []})
    
    def set_state(self, uid, flow, step, data, history=None):
        if history is None:
            history = user_states.get(uid, {}).get("history", [])
        state = {"flow": flow, "step": step, "data": data, "history": history}
        user_states[uid] = state
        if self.supabase:
            self.supabase.save_state(uid, state)
    
    def clear_state(self, uid):
        user_states.pop(uid, None)
        if self.supabase:
            self.supabase.clear_state(uid)
    
    def handle(self, uid, text, customer_name, biz_config, config):
        # Handle quick reply payloads
        original_text = text
        if "_" in text and text.isupper():
            if text.startswith("ROOM_"):
                text = text.replace("ROOM_", "").lower()
            elif text.startswith("GUESTS_"):
                text = text.replace("GUESTS_", "")
            elif text.startswith("WEDDING_"):
                text = text.replace("WEDDING_", "").lower()
            elif text.startswith("EVENT_"):
                text = text.replace("EVENT_", "").lower()
            elif text.startswith("PKG_"):
                text = text.replace("PKG_", "").lower()
            elif text.startswith("ALBUM_"):
                text = text.replace("ALBUM_", "").lower()
        
        state = self.get_state(uid)
        flow = state["flow"]
        lower = text.lower().strip()
        
        if lower in ["cancel", "exit", "stop", "kansela", "sardeng", "cancel_booking"]:
            self.clear_state(uid)
            return {"text": f"Cancelled, {customer_name}. Type BOOK to start again!", "quick_replies": [{"title": "📅 Book Again", "payload": "BOOK"}]}
        
        if lower in ["back", "bumalik", "ag-subli"]:
            history = state.get("history", [])
            if history:
                prev = history.pop()
                self.set_state(uid, prev["flow"], prev["step"], prev["data"], history)
                return {"text": f"Back to previous step. {prev.get('prompt', 'Please answer again:')}", "quick_replies": []}
        
        if flow is None:
            btype = biz_config.get("type", "photographer").lower()
            if btype == "resort":
                return self._start_resort(uid, customer_name, biz_config)
            elif btype in ["product", "shop"]:
                return self._start_product(uid, customer_name, biz_config)
            else:
                if any(k in lower for k in ["resort", "room", "villa"]):
                    return self._start_resort(uid, customer_name, biz_config)
                elif any(k in lower for k in ["buy", "order", "product", "shop"]):
                    return self._start_product(uid, customer_name, biz_config)
                else:
                    return self._start_photo(uid, customer_name, biz_config)
        
        if flow == "resort":
            return self._handle_resort(uid, text, customer_name, biz_config, config)
        if flow == "photographer":
            return self._handle_photo(uid, text, customer_name, biz_config, config)
        if flow == "product":
            return self._handle_product(uid, text, customer_name, biz_config, config)
    
    # RESORT
    def _start_resort(self, uid, customer_name, biz):
        self.set_state(uid, "resort", "checkin", {}, [])
        text = f"🏖️ Resort Booking at {biz.get('name')}!\n\nRooms:\n🏠 Standard 2pax ₱2,500\n✨ Deluxe 3pax ₱3,500\n👨‍👩‍👧 Family 5pax ₱5,000\n🎉 Barkada 10pax ₱8,000\n\nWhen is check-in?"
        quick = [{"title": "Today", "payload": "Today"}, {"title": "Tomorrow", "payload": "Tomorrow"}, {"title": "Next Week", "payload": "Next Week"}]
        return {"text": text, "quick_replies": quick}
    
    def _handle_resort(self, uid, text, customer_name, biz, config):
        state = self.get_state(uid)
        step, data, history = state["step"], state["data"], state.get("history", [])
        
        def save_hist(curr_step, curr_data, prompt):
            history.append({"flow": "resort", "step": curr_step, "data": curr_data.copy(), "prompt": prompt})
            return history
        
        def extract_guests(t):
            nums = re.findall(r'\d+', t)
            if nums:
                try:
                    n = int(nums[0])
                    if 1 <= n <= 50:
                        return str(n)
                except: pass
            word_map = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10", "isa": "1", "dalawa": "2", "tatlo": "3", "maysa": "1", "dua": "2", "tallo": "3"}
            lt = t.lower()
            for w, num in word_map.items():
                if w in lt:
                    return num
            return None
        
        def extract_room_type(t):
            lt = t.lower()
            if any(k in lt for k in ["standard", "stan"]): return "standard"
            if any(k in lt for k in ["deluxe", "delux"]): return "deluxe"
            if any(k in lt for k in ["family", "fami", "villa"]): return "family"
            if any(k in lt for k in ["barkada", "bark", "whole", "buong", "entire", "group"]): return "barkada"
            return None

        if step == "checkin":
            h = save_hist("checkin", data, "check-in")
            data["checkin"] = text.strip()
            self.set_state(uid, "resort", "checkout", data, h)
            return {"text": f"Check-in: {text} 📅\nWhen is check-out?", "quick_replies": [{"title": "Next Day", "payload": "Next Day"}, {"title": "Dec 26", "payload": "Dec 26"}, {"title": "2 Nights", "payload": "2 nights"}]}
        
        if step == "checkout":
            guests = extract_guests(text)
            room = extract_room_type(text)
            if guests and not room:
                data["checkout"] = "Not specified"
                data["guests"] = guests
                h = save_hist("checkout", {"checkin": data["checkin"]}, "check-out")
                self.set_state(uid, "resort", "room_type", data, h)
                return {"text": f"{guests} guests! 👥\nWhich room type?", "quick_replies": [{"title": "Standard ₱2.5k", "payload": "ROOM_STANDARD"}, {"title": "Deluxe ₱3.5k", "payload": "ROOM_DELUXE"}, {"title": "Family ₱5k", "payload": "ROOM_FAMILY"}, {"title": "Barkada ₱8k", "payload": "ROOM_BARKADA"}]}
            h = save_hist("checkout", {"checkin": data["checkin"]}, "check-out")
            data["checkout"] = text.strip()
            self.set_state(uid, "resort", "guests", data, h)
            return {"text": f"Check-out: {text} 📅\nHow many guests?", "quick_replies": [{"title": "2 Guests", "payload": "GUESTS_2"}, {"title": "3 Guests", "payload": "GUESTS_3"}, {"title": "5 Guests", "payload": "GUESTS_5"}, {"title": "10 Guests", "payload": "GUESTS_10"}]}
        
        if step == "guests":
            guests = extract_guests(text)
            if not guests:
                room = extract_room_type(text)
                if room:
                    data["guests"] = "2"
                    data["room_type"] = room
                    data["price"] = config.RESORT_ROOMS[room]["price"]
                    h = save_hist("guests", {"checkin": data["checkin"], "checkout": data["checkout"]}, "guests")
                    self.set_state(uid, "resort", "name", data, h)
                    return {"text": f"{config.RESORT_ROOMS[room]['name']} - ₱{config.RESORT_ROOMS[room]['price']}/night!\nFull name?", "quick_replies": []}
                return {"text": f"How many guests? Example: 2, 5, 10", "quick_replies": [{"title": "2 Guests", "payload": "GUESTS_2"}, {"title": "5 Guests", "payload": "GUESTS_5"}, {"title": "10 Guests", "payload": "GUESTS_10"}]}
            h = save_hist("guests", {"checkin": data["checkin"], "checkout": data["checkout"]}, "guests")
            data["guests"] = guests
            self.set_state(uid, "resort", "room_type", data, h)
            return {"text": f"{guests} guests! 👥\nWhich room type?", "quick_replies": [{"title": "Standard ₱2.5k", "payload": "ROOM_STANDARD"}, {"title": "Deluxe ₱3.5k", "payload": "ROOM_DELUXE"}, {"title": "Family ₱5k", "payload": "ROOM_FAMILY"}, {"title": "Barkada ₱8k", "payload": "ROOM_BARKADA"}]}
        
        if step == "room_type":
            room = extract_room_type(text)
            if not room:
                guests = extract_guests(text)
                if guests:
                    data["guests"] = guests
                    return {"text": f"Updated guests to {guests}! Now room type?", "quick_replies": [{"title": "Standard ₱2.5k", "payload": "ROOM_STANDARD"}, {"title": "Deluxe ₱3.5k", "payload": "ROOM_DELUXE"}, {"title": "Family ₱5k", "payload": "ROOM_FAMILY"}, {"title": "Barkada ₱8k", "payload": "ROOM_BARKADA"}]}
                return {"text": f"Please choose room type", "quick_replies": [{"title": "Standard ₱2.5k", "payload": "ROOM_STANDARD"}, {"title": "Deluxe ₱3.5k", "payload": "ROOM_DELUXE"}, {"title": "Family ₱5k", "payload": "ROOM_FAMILY"}, {"title": "Barkada ₱8k", "payload": "ROOM_BARKADA"}]}
            h = save_hist("room_type", {"checkin": data["checkin"], "checkout": data["checkout"], "guests": data["guests"]}, "room")
            data["room_type"] = room
            data["price"] = config.RESORT_ROOMS[room]["price"]
            self.set_state(uid, "resort", "name", data, h)
            return {"text": f"Great! {config.RESORT_ROOMS[room]['name']} - ₱{config.RESORT_ROOMS[room]['price']}/night! 🏠\nWhat's your full name?", "quick_replies": []}
        
        if step == "name":
            if len(text.strip()) < 2:
                return {"text": "Full name please? Example: Juan Dela Cruz", "quick_replies": []}
            h = save_hist("name", {"checkin": data["checkin"], "checkout": data["checkout"], "guests": data["guests"], "room_type": data["room_type"]}, "name")
            data["name"] = text.strip()
            self.set_state(uid, "resort", "phone", data, h)
            return {"text": f"Thanks {text}! Phone number? (09123456789)", "quick_replies": []}
        
        if step == "phone":
            phone_digits = re.sub(r'\D', '', text)
            if len(phone_digits) < 7:
                return {"text": f"Valid phone please? Example: 09123456789", "quick_replies": []}
            data["phone"] = text.strip()
            bid = f"RESORT-{str(uuid.uuid4())[:8].upper()}"
            data.update({"booking_id": bid, "type": "resort", "business": biz.get('name'), "page_id": biz.get('page_id'), "created_at": datetime.now().isoformat(), "status": "pending", "user_id": uid, "customer_name": customer_name})
            bookings[bid] = data
            save_bookings()
            if self.supabase:
                self.supabase.save_booking(data)
            self.clear_state(uid)
            room = config.RESORT_ROOMS.get(data["room_type"], {})
            text_out = f"✅ Resort Booking!\n📋 {bid}\n🏖️ {biz.get('name')}\n👤 {data['name']} 📱 {data['phone']}\n📅 {data['checkin']} to {data['checkout']}\n👥 {data['guests']} guests\n🏠 {room.get('name', data['room_type'])} ₱{data['price']}/night\n\nStaff will confirm within 1hr. Type BOOKING {bid}"
            return {"text": text_out, "quick_replies": [{"title": "📋 My Bookings", "payload": "MY_BOOKINGS"}, {"title": "📅 Book Again", "payload": "BOOK"}]}

    # PHOTO
    def _start_photo(self, uid, customer_name, biz):
        self.set_state(uid, "photographer", "event_type", {}, [])
        return {"text": f"📸 Photography Booking at {biz.get('name', 'Jeafred Photography')}, {customer_name}!\n\nWhat event?", "quick_replies": [{"title": "💍 Wedding", "payload": "EVENT_WEDDING"}, {"title": "💑 PreNup", "payload": "EVENT_PRENUP"}, {"title": "🎂 Birthday", "payload": "EVENT_BIRTHDAY"}, {"title": "🎓 Debut", "payload": "EVENT_DEBUT"}, {"title": "👨‍👩‍👧 Family", "payload": "EVENT_FAMILY"}, {"title": "🎓 Graduation", "payload": "EVENT_GRADUATION"}]}
    
    def _handle_photo(self, uid, text, customer_name, biz, config):
        state = self.get_state(uid)
        step, data = state["step"], state["data"]
        lower = text.lower()
        if step == "event_type":
            data["event_type"] = text.upper()
            if "wedding" in lower:
                self.set_state(uid, "photographer", "wedding_package", data, [])
                return {"text": f"Wedding! 💍 Choose package:\n🥇 Gold 40k (2P 3V 1SDE)\n🥈 Silver 25k (1P 2V)\n🥉 Bronze 18k (1P 1V)", "quick_replies": [{"title": "🥇 Gold 40k", "payload": "WEDDING_GOLD"}, {"title": "🥈 Silver 25k", "payload": "WEDDING_SILVER"}, {"title": "🥉 Bronze 18k", "payload": "WEDDING_BRONZE"}]}
            else:
                self.set_state(uid, "photographer", "date", data, [])
                return {"text": f"{text} noted! When is event date? (e.g., Dec 30)", "quick_replies": [{"title": "This Week", "payload": "This Week"}, {"title": "Next Week", "payload": "Next Week"}, {"title": "Dec 30", "payload": "Dec 30"}]}
        if step == "wedding_package":
            pkg = "gold" if "gold" in lower else "silver" if "silver" in lower else "bronze" if "bronze" in lower else None
            if not pkg:
                return {"text": "Choose wedding package:", "quick_replies": [{"title": "🥇 Gold 40k", "payload": "WEDDING_GOLD"}, {"title": "🥈 Silver 25k", "payload": "WEDDING_SILVER"}, {"title": "🥉 Bronze 18k", "payload": "WEDDING_BRONZE"}]}
            data["wedding_package"] = pkg
            data["price"] = config.WEDDING_PACKAGES[pkg]["price"]
            data["package"] = config.WEDDING_PACKAGES[pkg]["name"]
            data["team"] = config.WEDDING_PACKAGES[pkg]["team"]
            self.set_state(uid, "photographer", "date", data, [])
            return {"text": f"Great! {data['package']} - ₱{data['price']}\nWhen is wedding date?", "quick_replies": [{"title": "Dec 25", "payload": "Dec 25"}, {"title": "Jan 15", "payload": "Jan 15"}]}
        if step == "date":
            data["date"] = text
            self.set_state(uid, "photographer", "time", data, [])
            return {"text": f"Date: {text}\nWhat time?", "quick_replies": [{"title": "8AM", "payload": "8AM"}, {"title": "2PM", "payload": "2PM"}, {"title": "Whole Day", "payload": "Whole Day"}]}
        if step == "time":
            data["time"] = text
            self.set_state(uid, "photographer", "location", data, [])
            return {"text": f"Time: {text}\nVenue/location?", "quick_replies": []}
        if step == "location":
            data["location"] = text
            if "wedding_package" not in data:
                self.set_state(uid, "photographer", "service", data, [])
                return {"text": f"Location: {text}\nWhat service?", "quick_replies": [{"title": "📸 Photo 3.5k", "payload": "PKG_PHOTOGRAPHER"}, {"title": "🎥 Video 7k", "payload": "PKG_VIDEOGRAPHER"}, {"title": "🚁 Drone 5k", "payload": "PKG_DRONE"}, {"title": "✂️ SDE 6.5k", "payload": "PKG_SDE"}]}
            else:
                self.set_state(uid, "photographer", "addon", data, [])
                return {"text": f"Location: {text}\nAdd-on Album?", "quick_replies": [{"title": "Album 30p ₱5.5k", "payload": "ALBUM_30"}, {"title": "Album 20p ₱4k", "payload": "ALBUM_20"}, {"title": "Album 10p ₱3k", "payload": "ALBUM_10"}, {"title": "None", "payload": "ALBUM_NONE"}]}
        if step == "service":
            data["service_type"] = text
            price = 3500
            if "video" in lower and "photo" in lower: price = 10500
            elif "video" in lower: price = 7000
            elif "drone" in lower: price = 5000
            elif "sde" in lower: price = 6500
            data["price"] = price
            data["package"] = text
            self.set_state(uid, "photographer", "addon", data, [])
            return {"text": f"Service: {text} - ₱{price}\nAdd-on Album?", "quick_replies": [{"title": "Album 30p ₱5.5k", "payload": "ALBUM_30"}, {"title": "Album 20p ₱4k", "payload": "ALBUM_20"}, {"title": "Album 10p ₱3k", "payload": "ALBUM_10"}, {"title": "None", "payload": "ALBUM_NONE"}]}
        if step == "addon":
            if "album" in lower and "none" not in lower:
                data["addon"] = text.upper()
                if "30" in text: data["addon_price"] = 5500
                elif "20" in text: data["addon_price"] = 4000
                elif "10" in text: data["addon_price"] = 3000
                else: data["addon_price"] = 0
            else:
                data["addon"] = "None"
                data["addon_price"] = 0
            self.set_state(uid, "photographer", "name", data, [])
            return {"text": f"Add-on: {data['addon']}\nFull name?", "quick_replies": []}
        if step == "name":
            data["name"] = text
            self.set_state(uid, "photographer", "phone", data, [])
            return {"text": f"Thanks {text}! Phone number?", "quick_replies": []}
        if step == "phone":
            data["phone"] = text
            bid = f"PHOTO-{str(uuid.uuid4())[:8].upper()}"
            total = data.get("price", 0) + data.get("addon_price", 0)
            data.update({"booking_id": bid, "type": "photographer", "business": biz.get('name'), "page_id": biz.get('page_id'), "created_at": datetime.now().isoformat(), "status": "pending", "user_id": uid, "total": total})
            bookings[bid] = data
            save_bookings()
            if self.supabase:
                self.supabase.save_booking(data)
            self.clear_state(uid)
            addon_str = f"\n📚 {data.get('addon')} ₱{data.get('addon_price')}" if data.get('addon_price', 0) > 0 else ""
            return {"text": f"✅ Photo Booking!\n📋 {bid}\n📸 {biz.get('name')}\n👤 {data['name']} 📱 {data['phone']}\n🎉 {data.get('event_type')} {data.get('package')} ₱{data.get('price')}{addon_str}\n📅 {data.get('date')} at {data.get('time')}\n📍 {data.get('location')}\n💰 Total ₱{total}\nStaff will confirm. BOOKING {bid}", "quick_replies": [{"title": "📋 My Bookings", "payload": "MY_BOOKINGS"}, {"title": "📸 Book Again", "payload": "BOOK"}]}

    def _start_product(self, uid, customer_name, biz):
        self.set_state(uid, "product", "product", {}, [])
        return {"text": f"🛒 Order at {biz.get('name')}! What product?", "quick_replies": []}
    def _handle_product(self, uid, text, customer_name, biz, config):
        state = self.get_state(uid)
        step, data = state["step"], state["data"]
        if step == "product":
            data["product"] = text
            self.set_state(uid, "product", "quantity", data, [])
            return {"text": f"{text} noted! How many?", "quick_replies": [{"title": "1 pc", "payload": "1"}, {"title": "2 pcs", "payload": "2"}, {"title": "5 pcs", "payload": "5"}]}
        if step == "quantity":
            data["quantity"] = text
            self.set_state(uid, "product", "address", data, [])
            return {"text": "Delivery address?", "quick_replies": []}
        if step == "address":
            data["address"] = text
            self.set_state(uid, "product", "name", data, [])
            return {"text": "Full name?", "quick_replies": []}
        if step == "name":
            data["name"] = text
            self.set_state(uid, "product", "phone", data, [])
            return {"text": "Phone number?", "quick_replies": []}
        if step == "phone":
            data["phone"] = text
            bid = f"ORDER-{str(uuid.uuid4())[:8].upper()}"
            data.update({"booking_id": bid, "type": "product", "business": biz.get('name'), "page_id": biz.get('page_id'), "created_at": datetime.now().isoformat(), "status": "pending", "user_id": uid})
            bookings[bid] = data
            save_bookings()
            if self.supabase:
                self.supabase.save_booking(data)
            self.clear_state(uid)
            return {"text": f"✅ Order! 📋 {bid}\n{data['product']} x {data['quantity']}\n📍 {data['address']}\n👤 {data['name']} 📱 {data['phone']}", "quick_replies": [{"title": "📋 My Orders", "payload": "MY_BOOKINGS"}]}

    def get_booking(self, bid):
        if self.supabase:
            b = self.supabase.get_booking(bid)
            if b:
                return b
        return bookings.get(bid.upper())
    def list_user_bookings(self, uid):
        if self.supabase:
            supa = self.supabase.list_user_bookings(uid)
            if supa:
                return supa
        return [b for b in bookings.values() if b.get("user_id") == uid]
    def get_all_bookings(self, page_id=None):
        if self.supabase:
            supa = self.supabase.get_all_bookings(page_id)
            if supa:
                return supa
        return list(bookings.values())