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


def get_full_record() -> list:
    return get_client().table("prediction_record").select("*").order("game_date", desc=True).execute().data


def delete_all_records():
    get_client().table("prediction_record").delete().neq("game_id", "").execute()


def get_points_record() -> dict:
    rows = get_client().table("points_record").select("correct").execute().data
    wins = sum(1 for r in rows if r["correct"])
    losses = sum(1 for r in rows if not r["correct"])
    return {"wins": wins, "losses": losses, "total": wins + losses}


def get_full_points_record() -> list:
    return get_client().table("points_record").select("*").order("game_date", desc=True).execute().data


def delete_all_points_records():
    get_client().table("points_record").delete().neq("game_id", "").execute()


def save_points_result(game_id: str, game_date: str, projected_total: float, actual_total: float, correct: bool):
    client = get_client()
    existing = client.table("points_record").select("game_id").eq("game_id", game_id).execute().data
    if existing:
        client.table("points_record").update({
            "projected_total": projected_total,
            "actual_total": actual_total,
            "correct": correct,
        }).eq("game_id", game_id).execute()
    else:
        client.table("points_record").insert({
            "game_id": game_id,
            "game_date": game_date,
            "projected_total": projected_total,
            "actual_total": actual_total,
            "correct": correct,
        }).execute()


def save_game_result(game_id: str, game_date: str, predicted_winner: str, actual_winner: str, correct: bool):
    client = get_client()
    existing = client.table("prediction_record").select("game_id").eq("game_id", game_id).execute().data
    if existing:
        client.table("prediction_record").update({
            "predicted_winner": predicted_winner,
            "actual_winner": actual_winner,
            "correct": correct,
        }).eq("game_id", game_id).execute()
    else:
        client.table("prediction_record").insert({
            "game_id": game_id,
            "game_date": game_date,
            "predicted_winner": predicted_winner,
            "actual_winner": actual_winner,
            "correct": correct,
        }).execute()
