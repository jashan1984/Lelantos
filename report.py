import os, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client

# Initialize clients
supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
client = TelegramClient(StringSession(os.environ['TELEGRAM_SESSION']), 
                        int(os.environ['TELEGRAM_API_ID']), 
                        os.environ['TELEGRAM_API_HASH'])

async def send_report():
    print("Fetching data from Supabase...")
    # Using the correct table name 'tips' that we just created
    response = supabase.table('tips').select('*').execute()
    tips = response.data
    
    wins = len([t for t in tips if t.get('status') == 'WON']) 
    losses = len([t for t in tips if t.get('status') == 'LOST'])
    pending = len([t for t in tips if t.get('status') == 'PENDING'])
    total_completed = wins + losses
    
    report_text = (
        "--- 📊 DAILY CRICKET BOT REPORT ---\n"
        f"Total Completed Matches: {total_completed}\n"
        f"Matches Pending: {pending}\n"
        f"Wins: {wins}\n"
        f"Losses: {losses}\n"
    )
    if total_completed > 0:
        report_text += f"Win Rate: {(wins/total_completed)*100:.2f}%\n"
    else:
        report_text += "Win Rate: N/A (No completed matches yet)\n"
    
    # Send directly to your 'Saved Messages' in Telegram
    print("Connecting to Telegram to send report...")
    await client.start()
    await client.send_message('me', report_text)
    print("✅ Report successfully sent to your Telegram Saved Messages.")

if __name__ == "__main__":
    asyncio.run(send_report())
