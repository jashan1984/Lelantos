import os
import json
import requests
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client

# Environment Variables Validation
TELEGRAM_SESSION = os.environ.get('TELEGRAM_SESSION')
TELEGRAM_API_ID = int(os.environ.get('TELEGRAM_API_ID', 0))
TELEGRAM_API_HASH = os.environ.get('TELEGRAM_API_HASH')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
MY_CHAT_ID = 'me'  # Sends alerts straight to your Telegram Saved Messages

# Initialize Clients
client = TelegramClient(StringSession(TELEGRAM_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

channels = ['@solutionhubcricket', '@Honey_punjabi_cricket0', '@cricket_aryan_betting_guruji']

def analyze_with_groq(text):
    """Fires a parsing request to Groq LLM and strips markdown blocks from JSON string safely."""
    prompt = (
        "Analyze this sports bet update text and convert it into a strict raw JSON. "
        "Do not include any extra introductory text. Only return keys:\n"
        "- trade_type (e.g., Match Winner, Toss, Spam/Promo)\n"
        "- target (e.g., team name like India, Australia, or None)\n"
        "- action (e.g., BUY, SELL, WON, LOST, PENDING)\n"
        "- price (odds limit/price, default to '0')\n"
        "- limit_size (stake percentage/limit size, default to '0')\n\n"
        f"Text to evaluate:\n{text}"
    )
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama3-70b-8192", 
                "messages": [{"role": "user", "content": prompt}], 
                "temperature": 0
            }
        )
        content = resp.json()['choices'][0]['message']['content'].strip()
        
        # Strip potential LLM markdown wraps
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        return json.loads(content.strip())
    except Exception as e:
        print(f"❌ Groq Parsing Error: {e}")
        return {"trade_type": "Error"}

async def main():
    await client.start()
    print("🚀 Oppenheimer Engine Online. Commencing scan...")
    
    for channel in channels:
        print(f"📡 Scanning {channel}...")
        try:
            # Check the last 3 messages to catch rapid updates
            async for message in client.iter_messages(channel, limit=3): 
                if not message.text: 
                    continue
                
                parsed = analyze_with_groq(message.text)
                trade_type = parsed.get("trade_type", "Error")
                
                # Filter out the noise (Spam, simple toss updates, and errors)
                if trade_type not in ["Spam/Promo", "Toss", "Error"]:
                    
                    # 1. Save quantitative data to Supabase
                    supabase.table('parsed_tips').insert({
                        "channel": channel,
                        "trade_type": trade_type,
                        "target": parsed.get("target"),
                        "action": parsed.get("action"),
                        "price": str(parsed.get("price", "0")),
                        "limit_size": str(parsed.get("limit_size", "0"))
                    }).execute()
                    
                    # 2. Fire Alert to your Telegram Saved Messages
                    alert = (
                        f"⚡ **OPPENHEIMER ALERT** ⚡\n\n"
                        f"📊 **Type:** {trade_type}\n"
                        f"🎯 **Target:** {parsed.get('target')}\n"
                        f"⚙️ **Action:** {parsed.get('action')}\n"
                        f"💰 **Price:** {parsed.get('price')}\n"
                        f"⚖️ **Stake:** {parsed.get('limit_size')}\n\n"
                        f"📡 **Source:** {channel}"
                    )
                    await client.send_message(MY_CHAT_ID, alert)
                    print(f"✅ Executed trade log and alert for {channel}")
                else:
