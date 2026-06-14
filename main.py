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
MY_CHAT_ID = 'me'  # Automatically sends alert messages to your Telegram Saved Messages

# Initialize Clients
client = TelegramClient(StringSession(TELEGRAM_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Target Telegram Channels to scan
channels = ['@solutionhubcricket', '@Honey_punjabi_cricket0', '@cricket_aryan_betting_guruji']

def auto_init_db():
    """Initializes the database table 'parsed_tips' if it does not already exist."""
    query = """
    CREATE TABLE IF NOT EXISTS parsed_tips (
        id SERIAL PRIMARY KEY,
        channel TEXT,
        trade_type TEXT,
        target TEXT,
        action TEXT,
        price TEXT,
        limit_size TEXT,
        timestamp TIMESTAMPTZ DEFAULT NOW()
    );
    """
    try:
        supabase.rpc('execute_sql', {'query': query}).execute()
        print("✅ Database Table 'parsed_tips' verified/initialized.")
    except Exception as e:
        print(f"⚠️ Table verification status: {e}")

def analyze_with_groq(text):
    """Sends the raw message text to Groq LLM to convert unstructured text to structured JSON."""
    prompt = (
        "Analyze this sports bet update text and convert it into strict raw JSON. "
        "Do not include any extra conversational text or formatting outside raw JSON. Only return these keys:\n"
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
        
        # Strip potential markdown code blocks wrapped around the JSON response
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        return json.loads(content.strip())
    except Exception as e:
        print(f"❌ Groq Parsing Error: {e}")
        return {"trade_type": "Error"}

async def main():
    # Make sure database is ready
    auto_init_db()
    
    # Start the user client
    await client.start()
    print("🚀 Oppenheimer Engine Online. Commencing channel scan...")
    
    for channel in channels:
        print(f"📡 Scanning {channel}...")
        try:
            # Scan the last 3 messages from each target channel
            async for message in client.iter_messages(channel, limit=3): 
                if not message.text: 
                    continue
                
                parsed = analyze_with_groq(message.text)
                trade_type = parsed.get("trade_type", "Error")
                
                # Filter out spam, simple toss reports, and API errors
                if trade_type not in ["Spam/Promo", "Toss", "Error"]:
                    
                    # 1. Log the trade parameters to Supabase
                    supabase.table('parsed_tips').insert({
                        "channel": channel,
                        "trade_type": trade_type,
                        "target": parsed.get("target"),
                        "action": parsed.get("action"),
                        "price": str(parsed.get("price", "0")),
                        "limit_size": str(parsed.get("limit_size", "0"))
                    }).execute()
                    
                    # 2. Forward a formatted Alert immediately to your Telegram 'Saved Messages'
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
                    print(f"✅ Logged and alerted successfully for {channel}")
                else:
                    print(f"⏩ Ignored noise category: {trade_type}")
                    
        except Exception as e:
            print(f"❌ Error scanning channel {channel}: {e}")

if __name__ == "__main__":
    client.loop.run_until_complete(main())
