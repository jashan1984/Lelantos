import os
from supabase import create_client

supabase = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

def get_stats():
    tips = supabase.table('tips').select('*').execute().data
    wins = len([t for t in tips if t['status'] == 'WON'])
    losses = len([t for t in tips if t['status'] == 'LOST'])
    total = wins + losses
    
    print("--- BETTING PERFORMANCE REPORT ---")
    print(f"Total Completed Tips: {total}")
    print(f"Wins: {wins}")
    print(f"Losses: {losses}")
    if total > 0:
        print(f"Win Rate: {(wins/total)*100:.2f}%")

if __name__ == "__main__":
    get_stats()