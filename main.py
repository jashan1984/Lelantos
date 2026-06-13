import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client

# Load secrets from GitHub Environment
api_id = int(os.environ['TELEGRAM_API_ID'])
api_hash = os.environ['TELEGRAM_API_HASH']
session_str = os.environ['TELEGRAM_SESSION']
bot_token = os.environ['TELEGRAM_BOT_TOKEN']
supabase_url = os.environ['SUPABASE_URL']
supabase_key = os.environ['SUPABASE_KEY']
chat_id = int(os.environ['MY_TELEGRAM_CHAT_ID'])

# Initialize clients
client = TelegramClient(StringSession(session_str), api_id, api_hash)
supabase = create_client(supabase_url, supabase_key)

# The list of channels to monitor
channels = ['@solutionhubcricket', '@DollyCricketTips', '@Honey_punjabi_cricket0', '@cricket_aryan_betting_guruji', '@cbtfspeednewstips']

async def main():
    print("Starting tracker...")
    async for message in client.iter_messages(channels, limit=5):
        # Here is where we will add the logic to parse tips with Groq
        # and insert them into your Supabase database.
        print(f"New message from {message.chat.title}: {message.text}")

    await client.send_message(chat_id, "Tracker run completed successfully.")

with client:
    client.loop.run_until_complete(main())
