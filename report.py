import os
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
MY_CHAT_ID = 'me' # Automatically routes to your Saved Messages chat

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = TelegramClient(StringSession(TELEGRAM_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)

async def send_report():
    print("Fetching statistics from Supabase table 'parsed_tips'...")
    try:
        response = supabase.table('parsed_tips').select('*').execute()
        tips = response.data
    except Exception as e:
        print(f"❌ Failed to query database: {e}")
        return

    # Counting metrics based on parsed action statuses
    wins = len([t for t in tips if t.get('action') == 'WON']) 
    losses = len([t for t in tips if t.get('action') == 'LOST'])
    pending = len([t for t in tips if t.get('action') in ['PENDING', 'BUY', 'SELL']])
    total_completed = wins + losses
    
    report_text = (
        "--- 📊 DAILY CRICKET BOT REPORT ---\n"
        f"Total Completed Trades: {total_completed}\n"
        f"Trades Pending: {pending}\n"
        f"Wins: {wins}\n"
        f"Losses: {losses}\n"
    )
    if total_completed > 0:
        report_text += f"Win Rate: {(wins / total_completed) * 100:.2f}%\n"
    else:
        report_text += "Win Rate: N/A (No completed transactions found yet)\n"
    
    print("Connecting to Telegram...")
    await client.start()
    await client.send_message(MY_CHAT_ID, report_text)
    print("✅ Report successfully sent to your Telegram Saved Messages.")

if __name__ == "__main__":
    asyncio.run(send_report())
