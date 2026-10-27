from flask import Flask, request
import requests
import os

app = Flask(__name__)

PAGE_TOKEN = os.environ.get("PAGE_TOKEN", "").strip()
GROQ_KEY = os.environ.get("GROQ_KEY", "").strip()
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "jeafred_bot_123").strip()

def ask_ai(user_message):
    if not GROQ_KEY:
        return "AI key not set. Add GROQ_KEY in Render."
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": "You are a friendly AI for Jeafred's Facebook Page in Guimba. Reply short, helpful, in English or Taglish. You are a student-built bot."},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 400
            },
            timeout=25
        )
        data = r.json()
        if 'choices' in data and len(data['choices']) > 0:
            return data['choices'][0]['message']['content']
        else:
            print("Groq raw error:", data)
            return "Sorry, AI is busy. Try again! Error: " + str(data.get('error', {}).get('message','unknown'))
    except Exception as e:
        print("AI exception:", e)
        return f"Sorry, error: {e}"

@app.route('/')
def home():
    return "Messenger AI Bot is running! Use /api/messenger/webhook", 200

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
        print("Incoming webhook:", data)
        if data and data.get('object') == 'page':
            for entry in data.get('entry', []):
                for event in entry.get('messaging', []):
                    sender_id = event.get('sender', {}).get('id')
                    msg = event.get('message', {})
                    if sender_id and msg.get('text'):
                        user_text = msg['text']
                        print(f"Message from {sender_id}: {user_text}")
                        reply = ask_ai(user_text)
                        print(f"AI reply: {reply}")
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
                                print("Send exception:", e)
        return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
