import os
import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client

# Environment Variables Validation
TELEGRAM_SESSION = os.environ.get('TELEGRAM_SESSION')
TELEGRAM_API_ID = int(os.environ.get('TELEGRAM_API_ID', 0))
TELEGRAM_API_HASH = os.environ.get('TELEGRAM_API_HASH')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
MY_CHAT_ID = 'me'

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = TelegramClient(StringSession(TELEGRAM_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)

async def send_report():
    print("📡 Fetching statistics from Supabase...")
    try:
        response = supabase.table('parsed_tips').select('*').order('id', desc=True).limit(10).execute()
        tips = response.data
    except Exception as e:
        print(f"❌ Failed to query database: {e}")
        return

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
        report_text += f"Win Rate: {(wins / total_completed) * 100:.2f}%\n\n"
    else:
        report_text += "Win Rate: N/A\n\n"
        
    report_text += "📝 LATEST LOGGED TRADES BY TIPSTER:\n"
    if not tips:
        report_text += "• No trades captured in the database yet.\n"
    else:
        for t in tips:
            channel = t.get('channel', 'Unknown Source')
            trade_type = t.get('trade_type', 'N/A')
            target = t.get('target', 'N/A')
            action = t.get('action', 'N/A')
            price = t.get('price', '0')
            report_text += f"• 🎯 {target} ({trade_type}) | {action} @ {price}\n  └─ 📡 Source: {channel}\n\n"
    
    print("🔌 Connecting to Telegram Session...")
    try:
        # Force a 15-second strict timeout so the script cannot hang forever
        await asyncio.wait_for(client.connect(), timeout=15)
        
        if not await client.is_user_authorized():
            print("❌ Error: Telegram Session is invalid or unauthorized. Re-export your String Session.")
            return
            
        print("📤 Sending compiled report payload...")
        await client.send_message(MY_CHAT_ID, report_text)
        print("✅ Report successfully dispatched.")
    except asyncio.TimeoutError:
        print("❌ Timeout: Telegram connection timed out.")
    except Exception as e:
        print(f"❌ Telegram Communication Error: {e}")
    finally:
        # Always disconnect cleanly to kill the active runner thread
        await client.disconnect()
        print("🔌 Disconnected cleanly.")

if __name__ == "__main__":
    # Run the async loop and force-exit the process when done
    asyncio.run(send_report())
    sys.exit(0)
