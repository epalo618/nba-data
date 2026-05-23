from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import supabase_service, nba_service
from app.services.predictions_service import calculate_win_probability
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

router = APIRouter()


class GameResult(BaseModel):
    game_id: str
    predicted_winner: str
    actual_winner: str


def _eastern_today() -> str:
    return datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


@router.get("")
def get_record():
    try:
        return supabase_service.get_record()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
def submit_result(result: GameResult):
    try:
        correct = result.predicted_winner == result.actual_winner
        supabase_service.save_game_result(
            game_id=result.game_id,
            game_date=_eastern_today(),
            predicted_winner=result.predicted_winner,
            actual_winner=result.actual_winner,
            correct=correct,
        )
        return {"ok": True, "correct": correct}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
def sync_record():
    """Auto-submit completed games from yesterday and today."""
    try:
        all_teams = {t["id"]: t for t in nba_service.get_all_teams()}
        submitted = []

        eastern = ZoneInfo("America/New_York")
        today_str = datetime.now(eastern).strftime("%Y-%m-%d")
        yesterday_str = (datetime.now(eastern) - timedelta(days=1)).strftime("%Y-%m-%d")

        for date_str in [yesterday_str, today_str]:
            try:
                data = nba_service.get_games_for_date(date_str)
            except Exception:
                continue

            for game in data.get("games", []):
                if game.get("GAME_STATUS_ID") != 3:
                    continue
                home_id = game.get("HOME_TEAM_ID")
                away_id = game.get("VISITOR_TEAM_ID")
                home_score = game.get("HOME_SCORE", 0)
                away_score = game.get("VISITOR_SCORE", 0)
                if not home_id or not away_id or not home_score or not away_score:
                    continue
                if home_score == away_score:
                    continue

                home_info = all_teams.get(home_id, {})
                away_info = all_teams.get(away_id, {})
                home_name = home_info.get("full_name", f"{game.get('HOME_TEAM_CITY', '')} {game.get('HOME_TEAM_NAME', '')}".strip())
                away_name = away_info.get("full_name", f"{game.get('VISITOR_TEAM_CITY', '')} {game.get('VISITOR_TEAM_NAME', '')}".strip())

                try:
                    win_probs = calculate_win_probability(home_id, away_id, home_name, away_name)
                except Exception:
                    continue

                predicted = win_probs.get("favored_team")
                if not predicted:
                    continue

                actual = home_name if home_score > away_score else away_name
                correct = predicted == actual

                supabase_service.save_game_result(
                    game_id=game["GAME_ID"],
                    game_date=date_str,
                    predicted_winner=predicted,
                    actual_winner=actual,
                    correct=correct,
                )
                submitted.append({"game_id": game["GAME_ID"], "correct": correct})

        return {"synced": len(submitted), "results": submitted, **supabase_service.get_record()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
