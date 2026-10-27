from flask import Blueprint, request
import requests, logging, time
from ..config import Config
from .ai import AIService
from .booking_manager import BookingManager
logger = logging.getLogger(__name__)
messenger_bp = Blueprint('messenger', __name__)
booking_manager = BookingManager()
rate_limit = {}

@messenger_bp.route('/api/messenger/webhook', methods=['GET'])
def verify():
    config = Config()
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == config.VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@messenger_bp.route('/api/messenger/webhook', methods=['POST'])
@messenger_bp.route('/webhook', methods=['POST'])
def webhook():
    config = Config()
    ai_service = AIService()
    data = request.get_json()
    logger.info(f"Incoming: {data}")
    if not data or data.get('object') != 'page':
        return "EVENT_RECEIVED", 200
    for entry in data.get('entry', []):
        page_id = entry.get('id')
        biz_config = config.get_business_config(page_id)
        page_token = config.get_page_token(page_id)
        for event in entry.get('messaging', []):
            sender_id = event.get('sender', {}).get('id')
            if not sender_id or sender_id == entry.get('id'):
                continue
            message = event.get('message', {})
            if sender_id and message:
                # Handle quick reply payload or text
                user_text = message.get('text', '')
                quick_reply = message.get('quick_reply', {})
                if quick_reply:
                    payload = quick_reply.get('payload', '')
                    # Use payload as text if present, otherwise use text
                    if payload:
                        user_text = payload
                        logger.info(f"Quick reply payload: {payload}")
                
                if not user_text:
                    continue
                    
                now = time.time()
                if now - rate_limit.get(sender_id, 0) < 0.5:
                    continue
                rate_limit[sender_id] = now
                
                send_typing(sender_id, True, page_token)
                mark_seen(sender_id, page_token)
                customer_name = get_customer_name(sender_id, page_token) or "boss"
                lower = user_text.lower().strip()
                
                # Global quick reply handlers
                if lower == "book" or lower == "my_bookings" or lower == "my bookings":
                    if lower == "my_bookings":
                        user_text = "my bookings"
                        lower = "my bookings"
                
                if lower in ["cancel", "exit", "stop", "kansela", "sardeng", "cancel_booking"]:
                    booking_manager.clear_state(sender_id)
                    send_typing(sender_id, False, page_token)
                    send_message(sender_id, f"Cancelled, {customer_name}. Type BOOK to start again!", page_token, quick_replies=[{"title": "📅 Book Again", "payload": "BOOK"}])
                    continue
                
                if lower.startswith("booking "):
                    bid = user_text.split(" ", 1)[1].strip()
                    b = booking_manager.get_booking(bid)
                    if b:
                        reply = f"📋 {bid}: {b.get('type')} - {b.get('event_type', b.get('package', ''))} - {b.get('status')} - Total ₱{b.get('total', b.get('price', ''))}"
                    else:
                        reply = f"Booking {bid} not found."
                    send_typing(sender_id, False, page_token)
                    send_message(sender_id, reply, page_token)
                    continue
                
                if "my booking" in lower or "my order" in lower or "my bookings" in lower:
                    user_bookings = booking_manager.list_user_bookings(sender_id)
                    if user_bookings:
                        txt = f"Your bookings, {customer_name}:"
                        for b in user_bookings[-5:]:
                            txt += f"\n📋 {b['booking_id']}: {b.get('type')} {b.get('status')}"
                        reply = txt
                    else:
                        reply = f"No bookings yet, {customer_name}. Type BOOK!"
                    send_typing(sender_id, False, page_token)
                    send_message(sender_id, reply, page_token, quick_replies=[{"title": "📅 Book Now", "payload": "BOOK"}])
                    continue

                state = booking_manager.get_state(sender_id)
                is_booking = lower in ["book", "booking", "reserve", "order", "magbook", "resort", "photo", "photographer", "rates", "product", "shop"] or state["step"] is not None or any(k in lower for k in ["book", "reserve", "wedding", "prenup", "birthday", "debut"]) or "_" in user_text  # payload contains _

                if is_booking:
                    result = booking_manager.handle(sender_id, user_text, customer_name, biz_config, config)
                    # Handle both old format (string) and new format (dict with quick_replies)
                    if isinstance(result, dict):
                        text_out = result.get("text", "")
                        quick = result.get("quick_replies", [])
                    else:
                        text_out = result
                        quick = []
                    send_typing(sender_id, False, page_token)
                    send_message(sender_id, text_out, page_token, quick_replies=quick)
                    continue

                if any(k in lower for k in config.HUMAN_KEYWORDS):
                    send_typing(sender_id, False, page_token)
                    send_message(sender_id, f"Got it, {customer_name}! Connecting to team at {biz_config.get('name')}. Hours: {biz_config.get('hours')}. Please leave concern.", page_token, quick_replies=[{"title": "📞 Call Manager", "payload": "HUMAN"}, {"title": "📅 Book", "payload": "BOOK"}])
                    continue

                reply = ai_service.get_reply(user_text, customer_name, biz_config)
                send_typing(sender_id, False, page_token)
                # Add quick replies for general chat
                quick = [
                    {"title": "📅 Book", "payload": "BOOK"},
                    {"title": "💰 Rates", "payload": "RATES"},
                    {"title": "📋 My Bookings", "payload": "MY_BOOKINGS"},
                ]
                send_message(sender_id, reply, page_token, quick_replies=quick)

            postback = event.get('postback', {})
            if postback and sender_id:
                page_id = entry.get('id')
                page_token = config.get_page_token(page_id)
                biz_config = config.get_business_config(page_id)
                payload = postback.get('payload', '')
                if payload == 'GET_STARTED':
                    send_message(sender_id, f"Hi! Welcome to {biz_config.get('name')}! 📸🏖️\n\nI can book:\n🏖️ RESORT\n📸 PHOTOGRAPHER\n🛒 PRODUCT\n\nTap a button below:", page_token, quick_replies=[
                        {"title": "🏖️ Book Resort", "payload": "BOOK"},
                        {"title": "📸 Book Photo", "payload": "BOOK"},
                        {"title": "💰 Rates", "payload": "RATES"},
                    ])

    return "EVENT_RECEIVED", 200

def send_typing(rid, is_typing, token):
    if not token:
        return
    try:
        action = "typing_on" if is_typing else "typing_off"
        requests.post(f"https://graph.facebook.com/v20.0/me/messages?access_token={token}", json={"recipient": {"id": rid}, "sender_action": action}, timeout=5)
    except:
        pass

def mark_seen(rid, token):
    if not token:
        return
    try:
        requests.post(f"https://graph.facebook.com/v20.0/me/messages?access_token={token}", json={"recipient": {"id": rid}, "sender_action": "mark_seen"}, timeout=5)
    except:
        pass

def send_message(rid, text, token, quick_replies=None):
    if not token:
        logger.error("No token")
        return
    try:
        message_data = {"text": text[:2000]}
        if quick_replies:
            # Facebook quick replies format
            fb_quick = []
            for qr in quick_replies[:11]:  # FB max 11 quick replies
                title = qr.get("title", "")[:20]  # FB title max 20 chars
                payload = qr.get("payload", title)[:1000]
                fb_quick.append({
                    "content_type": "text",
                    "title": title,
                    "payload": payload
                })
            message_data["quick_replies"] = fb_quick
        
        r = requests.post(f"https://graph.facebook.com/v20.0/me/messages?access_token={token}", json={"recipient": {"id": rid}, "message": message_data}, timeout=10)
        logger.info(f"Send: {r.text[:300]}")
    except Exception as e:
        logger.error(f"Send error: {e}")

def get_customer_name(uid, token):
    if not token:
        return None
    try:
        r = requests.get(f"https://graph.facebook.com/v20.0/{uid}?fields=first_name&access_token={token}", timeout=5)
        return r.json().get('first_name')
    except:
        return None
