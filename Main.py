from flask import Flask, request
import requests
import os

app = Flask(__name__)

PAGE_TOKEN = os.environ.get("PAGE_TOKEN")
GROQ_KEY = os.environ.get("GROQ_KEY")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "jeafred_bot_123")

def ask_ai(user_message):
    if not GROQ_KEY:
        print("Missing GROQ_KEY")
        return "AI key not set yet. Add GROQ_KEY in Render environment variables."
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a friendly, helpful AI assistant for Jeafred's Facebook Page in Guimba. You are a student-built chatbot. Reply in English, can use a little Tagalog if the user uses Tagalog. Keep replies short (2-4 sentences), friendly, and helpful. If you don't know, say you will ask a human."},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=25
        )
        data = r.json()
        if 'choices' in data:
            return data['choices'][0]['message']['content']
        else:
            print("Groq error:", data)
            return "Sorry, AI is busy. Try again!"
    except Exception as e:
        print("AI error:", e)
        return "Sorry, I'm having trouble right now. Please try again!"

@app.route('/')
def home():
    return "Messenger AI Bot is running! Use /api/messenger/webhook for Facebook.", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook_short():
    return webhook_main()

@app.route('/api/messenger/webhook', methods=['GET', 'POST'])
def webhook_main():
    if request.method == 'GET':
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if token == VERIFY_TOKEN and challenge:
            print(f"Webhook verified! challenge={challenge}")
            return challenge, 200
        print(f"Verify failed: got token={token}, expected={VERIFY_TOKEN}")
        return "Verification failed", 403

    if request.method == 'POST':
        data = request.get_json()
        print("Incoming webhook:", data)
        if data and data.get('object') == 'page':
            for entry in data.get('entry', []):
                for event in entry.get('messaging', []):
                    sender_id = event.get('sender', {}).get('id')
                    message = event.get('message', {})
                    if sender_id and message.get('text'):
                        user_text = message['text']
                        print(f"Message from {sender_id}: {user_text}")
                        reply_text = ask_ai(user_text)
                        if PAGE_TOKEN and sender_id != event.get('recipient', {}).get('id'):
                            try:
                                send_res = requests.post(
                                    f"https://graph.facebook.com/v20.0/me/messages?access_token={PAGE_TOKEN}",
                                    json={
                                        "recipient": {"id": sender_id},
                                        "message": {"text": reply_text}
                                    },
                                    timeout=10
                                )
                                print("Send result:", send_res.text)
                            except Exception as e:
                                print("Send error:", e)
        return "EVENT_RECEIVED", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
