import os
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client, Client

# 1. Configuration from GitHub Secrets
API_ID = int(os.environ['TELEGRAM_API_ID'])
API_HASH = os.environ['TELEGRAM_API_HASH']
SESSION_STRING = os.environ['TELEGRAM_SESSION']
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']

# 2. Initialize Clients
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 3. Your Target Channels
channels = [
    '@solutionhubcricket', 
    '@DollyCricketTips', 
    '@Honey_punjabi_cricket0', 
    '@cricket_aryan_betting_guruji', 
    '@cbtfspeednewstips'
]

async def main():
    await client.start()
    print("Bot successfully connected to Telegram!")
    
    for channel in channels:
        print(f"Checking messages in: {channel}")
        try:
            # Fetch the last 5 messages from the channel
            async for message in client.iter_messages(channel, limit=5):
                if not message.text:
                    continue  # Skip empty messages or images without text
                
                print(f"Processing a message from {channel}...")
                
                # Insert raw message data into your Supabase 'messages' table
                # (Make sure your Supabase table has 'channel' and 'text' columns)
                data, count = supabase.table('messages').insert({
                    "channel": channel, 
                    "text": message.text
                }).execute()
                
        except Exception as e:
            print(f"Error processing channel {channel}: {e}")

if __name__ == "__main__":
    client.loop.run_until_complete(main())
