from flask import Flask, request
import requests
import os

app = Flask(__name__)

PAGE_TOKEN = os.environ.get("PAGE_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_KEY", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_KEY", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "jeafred_bot_123").strip()

def ask_gemini(user_message):
    if not GEMINI_KEY:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        r = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": f"You are a friendly AI for Jeafred's Page in Guimba. Reply short, friendly, in English or Taglish. User says: {user_message}"}]}],
                "generationConfig": {"maxOutputTokens": 400, "temperature": 0.7}
            },
            timeout=20
        )
        data = r.json()
        print(f"Gemini raw: {data}")
        if 'candidates' in data and len(data['candidates']) > 0:
            text = data['candidates'][0]['content']['parts'][0]['text']
            return text
        else:
            print(f"Gemini failed: {data}")
            return None
    except Exception as e:
        print(f"Gemini exception: {e}")
        return None

def ask_groq(user_message):
    if not GROQ_KEY:
        return None
    models = ["llama3-8b-8192", "gemma2-9b-it", "mixtral-8x7b-32768"]
    for model_name in models:
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are friendly AI for Jeafred's Page."},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 400
                },
                timeout=20
            )
            data = r.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content']
            print(f"Groq {model_name} failed: {data}")
        except Exception as e:
            print(f"Groq {model_name} error: {e}")
            continue
    return None

def ask_ai(user_message):
    # Try Gemini first (free and stable), then Groq
    reply = ask_gemini(user_message)
    if reply:
        return reply
    reply = ask_groq(user_message)
    if reply:
        return reply
    return "Hi boss! I'm online now but my AI brain is resting. Try again in 30 seconds - I'm a free student bot from Guimba! Syak man met!"

@app.route('/')
def home():
    return "Messenger AI Bot is running! Gemini + Groq ready!", 200

@app.route('/webhook', methods=['GET', 'POST'])
@app.route('/api/messenger/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if token == VERIFY_TOKEN and challenge:
            return challenge, 200
        return "Verification failed", 403
    if request.method == 'POST':
        data = request.get_json()
        print("Incoming:", data)
        if data and data.get('object') == 'page':
            for entry in data.get('entry', []):
                for event in entry.get('messaging', []):
                    sender_id = event.get('sender', {}).get('id')
                    msg = event.get('message', {})
                    if sender_id and msg.get('text'):
                        user_text = msg['text']
                        print(f"Message from {sender_id}: {user_text}")
                        reply = ask_ai(user_text)
                        print(f"Reply: {reply}")
                        if PAGE_TOKEN:
                            try:
                                send_url = f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_TOKEN}"
                                send_res = requests.post(
                                    send_url,
                                    json={"recipient": {"id": sender_id}, "message": {"text": reply}},
                                    timeout=10
                                )
                                print("Send result:", send_res.text)
                            except Exception as e:
                                print("Send error:", e)
        return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
