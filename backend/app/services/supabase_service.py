import os
from supabase import create_client

_client = None

def get_client():
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _client = create_client(url, key)
    return _client


def get_record() -> dict:
    rows = get_client().table("prediction_record").select("correct").execute().data
    wins = sum(1 for r in rows if r["correct"])
    losses = sum(1 for r in rows if not r["correct"])
    return {"wins": wins, "losses": losses, "total": wins + losses}


def save_game_result(game_id: str, game_date: str, predicted_winner: str, actual_winner: str, correct: bool):
    get_client().table("prediction_record").upsert({
        "game_id": game_id,
        "game_date": game_date,
        "predicted_winner": predicted_winner,
        "actual_winner": actual_winner,
        "correct": correct,
    }).execute()
