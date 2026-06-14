import os, json, requests, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from supabase import create_client

# Initialize Clients
client = TelegramClient(StringSession(os.environ['TELEGRAM_SESSION']), int(os.environ['TELEGRAM_API_ID']), os.environ['TELEGRAM_API_HASH'])
supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

def auto_init_db():
    """Ensures the 'tips' table exists in the database."""
    query = """
    CREATE TABLE IF NOT EXISTS tips (
        id SERIAL PRIMARY KEY,
        tipper_username TEXT,
        match_name TEXT,
        team_selection TEXT,
        bet_type TEXT,
        odds NUMERIC,
        status TEXT DEFAULT 'PENDING',
        timestamp TIMESTAMPTZ DEFAULT NOW()
    );
    """
    try:
        # Use RPC to ensure the table is created if it doesn't exist
        supabase.rpc('execute_sql', {'query': query}).execute()
    except Exception as e:
        print(f"Table check/creation status: {e}")

def parse_msg(text):
    """Uses Groq AI to extract betting details from Telegram messages."""
    prompt = f"Extract JSON only: match_name, team_selection, bet_type, odds, status (PENDING/WON/LOST). Text: {text}"
    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", 
        headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
        json={"model": "llama3-70b-8192", "messages": [{"role": "user", "content": prompt}], "temperature": 0})
    return json.loads(resp.json()['choices'][0]['message']['content'])

async def main():
    auto_init_db() 
    await client.start()
    channels = ['@solutionhubcricket', '@Honey_punjabi_cricket0', '@cricket_aryan_betting_guruji']
    
    for chan in channels:
        async for msg in client.iter_messages(chan, limit=3):
            if not msg.text: continue
            try:
                data = parse_msg(msg.text)
                if data.get('status') == 'PENDING':
                    # Insert new tip
                    supabase.table('tips').insert({
                        "tipper_username": chan, "match_name": data['match_name'],
                        "team_selection": data['team_selection'], "bet_type": data['bet_type'], "odds": data.get('odds', 0)
                    }).execute()
                else:
                    # Update status for existing match
                    supabase.table('tips').update({"status": data['status']}).eq("match_name", data['match_name']).execute()
            except Exception as e:
                print(f"Skipping msg: {e}")

if __name__ == "__main__":
    asyncio.run(main())
