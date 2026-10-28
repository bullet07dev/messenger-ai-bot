# Jeafred Enterprise Bot V2 - Production Architecture

## 🚀 What's New vs V1

| V1 (Prototype) | V2 (Enterprise) |
|---|---|
| /tmp/bookings.json (lost on sleep) | Supabase Postgres (persistent) |
| 1 Groq model, fails = "AI brain resting" | AI Router: Gemini Flash → Groq 3.1/3.3 → Rule (logs which used) |
| if "madi" in text | Intent Classifier + Language Detection + User Preference |
| No RAG, hallucinates prices | RAG with knowledge base, Qdrant ready |
| No observability | /health + message_logs + model_used tracking |
| 1 Page | Multi-tenant: PAGE_ID_1, PAGE_TOKEN_1, etc |

## 🏗️ Architecture

```
Messenger Webhook
  ↓ (verify signature with APP_SECRET)
Intent Classifier (0ms, free)
  ↓
BOOKING_FLOW → BookingManager (Supabase state + smart parsers)
FAQ → RAG (knowledge base + Qdrant)
CHIT_CHAT → AI Router (Gemini → Groq → Rule)
HUMAN → Handoff (pause auto-reply 30 mins)
  ↓
Send Message (with quick replies)
  ↓
Log to Supabase (which model, which language, intent)
```

## 🔧 Setup (5 mins)

1. **Render Env Vars (keep your existing):**
   - PAGE_ACCESS_TOKEN, VERIFY_TOKEN=jeafred_bot_123, GROQ_KEY=gsk_...
   - GEMINI_KEY must start with AIza... (get from aistudio.google.com/app/apikey) - your AQ... key is invalid

2. **Optional but Recommended - Supabase (Free, 2 mins):**
   - Go to supabase.com → New Project (free)
   - SQL Editor → Paste SQL from /admin dashboard
   - Project Settings → API → Copy URL + anon key
   - Add to Render: SUPABASE_URL, SUPABASE_KEY
   - Now bookings survive Render sleep!

3. **Deploy:**
   - Upload this ZIP to github.com/bullet07dev/messenger-ai-bot (replace all)
   - Render auto-deploys
   - Visit https://your-app.onrender.com/health → Should show "ok", groq "configured", gemini "configured" if AIza key
   - Visit https://your-app.onrender.com/admin → Enter VERIFY_TOKEN → See bookings

## 📊 Free Stack Limits

- Render 750hrs/mo (enough for 1 service)
- Supabase 500MB DB, 50k requests/mo (10k bookings)
- Groq 14k req/day
- Qdrant 1GB free (when you enable)
- Total $0

## 🔜 Next Incremental Builds

- Week 2: Qdrant RAG + Google Sheet sync
- Week 3: Vercel dashboard with charts (bookings by language, by room)
- Week 4: GCash payment link
- Week 5: Carousels (photo packages with images)
- Week 6: Broadcast promo to past bookers

## 🔑 Multi-Page

To add 2nd Page (e.g., Resort):
- Render → Environment → Add:
  - PAGE_ID_1=123456789 (your resort Page ID)
  - PAGE_TOKEN_1=EAA... (resort Page token)
  - PAGE_ID_2=... (photo Page)
  - PAGE_TOKEN_2=...
- One repo powers all Pages, each has own booking table filtered by page_id

## 🛡️ Security

- Add APP_SECRET from Facebook App → Settings → Basic → App Secret
- Add to Render env: APP_SECRET=...
- Now webhook verifies signature (enterprise security)