from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import supabase_service, nba_service
from app.services.predictions_service import calculate_win_probability, calculate_projected_total
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

router = APIRouter()

# Only track games on or after this date (when the tracker went live)
TRACKER_START_DATE = "2026-05-22"


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


@router.delete("/reset")
def reset_record():
    try:
        supabase_service.delete_all_records()
        return {"ok": True}
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


@router.get("/debug")
def debug_sync():
    """Show what the sync endpoint would submit, without writing anything."""
    try:
        all_teams = {t["id"]: t for t in nba_service.get_all_teams()}
        eastern = ZoneInfo("America/New_York")
        today_str = datetime.now(eastern).strftime("%Y-%m-%d")
        yesterday_str = (datetime.now(eastern) - timedelta(days=1)).strftime("%Y-%m-%d")

        output = []
        for date_str in [yesterday_str, today_str]:
            try:
                data = nba_service.get_games_for_date(date_str)
                games = data.get("games", [])
                for game in games:
                    home_id = game.get("HOME_TEAM_ID")
                    away_id = game.get("VISITOR_TEAM_ID")
                    home_info = all_teams.get(home_id, {})
                    away_info = all_teams.get(away_id, {})
                    home_name = home_info.get("full_name", "?")
                    away_name = away_info.get("full_name", "?")
                    entry = {
                        "date": date_str,
                        "game_id": game.get("GAME_ID"),
                        "status_id": game.get("GAME_STATUS_ID"),
                        "status_text": game.get("GAME_STATUS_TEXT"),
                        "home": home_name,
                        "away": away_name,
                        "home_score": game.get("HOME_SCORE"),
                        "away_score": game.get("VISITOR_SCORE"),
                    }
                    if game.get("GAME_STATUS_ID") == 3 and home_id and away_id:
                        try:
                            wp = calculate_win_probability(home_id, away_id, home_name, away_name)
                            entry["predicted_winner"] = wp.get("favored_team")
                            hs = game.get("HOME_SCORE", 0)
                            vs = game.get("VISITOR_SCORE", 0)
                            if hs and vs and hs != vs:
                                entry["actual_winner"] = home_name if hs > vs else away_name
                                entry["correct"] = entry["predicted_winner"] == entry["actual_winner"]
                        except Exception as ex:
                            entry["wp_error"] = str(ex)
                    output.append(entry)
            except Exception as ex:
                output.append({"date": date_str, "error": str(ex)})

        return {"dates_checked": [yesterday_str, today_str], "games": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
def sync_record():
    """Auto-submit completed games from the last 7 days using LeagueGameLog."""
    try:
        from collections import defaultdict
        all_teams = {t["id"]: t for t in nba_service.get_all_teams()}
        submitted = []

        eastern = ZoneInfo("America/New_York")
        dates = [
            (datetime.now(eastern) - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(7)
            if (datetime.now(eastern) - timedelta(days=i)).strftime("%Y-%m-%d") >= TRACKER_START_DATE
        ]

        for date_str in dates:
            rows = nba_service.get_team_game_results_for_date(date_str)
            if not rows:
                continue

            by_game: dict = defaultdict(list)
            for row in rows:
                by_game[row["GAME_ID"]].append(row)

            for game_id, teams in by_game.items():
                if len(teams) != 2:
                    continue

                # MATCHUP field: "OKC vs. SAS" = home, "OKC @ SAS" = away
                home_row = next((r for r in teams if "vs." in r.get("MATCHUP", "")), None)
                away_row = next((r for r in teams if " @ " in r.get("MATCHUP", "")), None)
                if not home_row or not away_row:
                    continue

                home_id = int(home_row["TEAM_ID"])
                away_id = int(away_row["TEAM_ID"])
                home_info = all_teams.get(home_id, {})
                away_info = all_teams.get(away_id, {})
                home_name = home_info.get("full_name", str(home_row.get("TEAM_NAME", "")))
                away_name = away_info.get("full_name", str(away_row.get("TEAM_NAME", "")))

                actual = home_name if home_row.get("WL") == "W" else away_name

                try:
                    win_probs = calculate_win_probability(home_id, away_id, home_name, away_name)
                except Exception:
                    continue

                predicted = win_probs.get("favored_team")
                if not predicted:
                    continue

                supabase_service.save_game_result(
                    game_id=str(game_id),
                    game_date=date_str,
                    predicted_winner=predicted,
                    actual_winner=actual,
                    correct=predicted == actual,
                )
                submitted.append({"game_id": str(game_id), "correct": predicted == actual})

        return {"synced": len(submitted), "results": submitted, **supabase_service.get_record()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/points")
def get_points_record():
    try:
        return supabase_service.get_points_record()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/points/reset")
def reset_points_record():
    try:
        supabase_service.delete_all_points_records()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/points/debug")
def debug_points_sync():
    """Show what the points sync would submit, without writing anything."""
    try:
        from collections import defaultdict
        eastern = ZoneInfo("America/New_York")
        dates = [
            (datetime.now(eastern) - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(7)
            if (datetime.now(eastern) - timedelta(days=i)).strftime("%Y-%m-%d") >= TRACKER_START_DATE
        ]

        output = []
        for date_str in dates:
            rows = nba_service.get_team_game_results_for_date(date_str)
            if not rows:
                output.append({"date": date_str, "note": "no rows returned"})
                continue

            by_game: dict = defaultdict(list)
            for row in rows:
                by_game[row["GAME_ID"]].append(row)

            for game_id, teams in by_game.items():
                if len(teams) != 2:
                    output.append({"date": date_str, "game_id": str(game_id), "note": f"unexpected team count: {len(teams)}"})
                    continue

                home_row = next((r for r in teams if "vs." in r.get("MATCHUP", "")), None)
                away_row = next((r for r in teams if " @ " in r.get("MATCHUP", "")), None)
                if not home_row or not away_row:
                    output.append({"date": date_str, "game_id": str(game_id), "note": "could not identify home/away"})
                    continue

                home_id = int(home_row["TEAM_ID"])
                away_id = int(away_row["TEAM_ID"])
                home_pts = float(home_row.get("PTS") or 0)
                away_pts = float(away_row.get("PTS") or 0)
                actual_total = home_pts + away_pts

                entry: dict = {
                    "date": date_str,
                    "game_id": str(game_id),
                    "home": home_row.get("TEAM_NAME"),
                    "away": away_row.get("TEAM_NAME"),
                    "home_pts": home_pts,
                    "away_pts": away_pts,
                    "actual_total": actual_total,
                }

                if actual_total == 0:
                    entry["note"] = "skipped: actual_total is 0"
                    output.append(entry)
                    continue

                try:
                    proj_total = float(calculate_projected_total(home_id, away_id))
                    entry["proj_total"] = proj_total
                    entry["correct"] = actual_total >= proj_total
                except Exception as ex:
                    entry["proj_error"] = str(ex)

                output.append(entry)

        try:
            db_record = supabase_service.get_points_record()
        except Exception as ex:
            db_record = {"error": str(ex)}

        return {"dates_checked": dates, "games": output, "current_db_record": db_record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/points/sync")
def sync_points_record():
    """Auto-submit completed games' projected vs actual total points from last 7 days."""
    try:
        from collections import defaultdict
        submitted = []
        errors = []
        eastern = ZoneInfo("America/New_York")
        dates = [
            (datetime.now(eastern) - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(7)
            if (datetime.now(eastern) - timedelta(days=i)).strftime("%Y-%m-%d") >= TRACKER_START_DATE
        ]

        for date_str in dates:
            rows = nba_service.get_team_game_results_for_date(date_str)
            if not rows:
                continue

            by_game: dict = defaultdict(list)
            for row in rows:
                by_game[row["GAME_ID"]].append(row)

            for game_id, teams in by_game.items():
                if len(teams) != 2:
                    continue

                home_row = next((r for r in teams if "vs." in r.get("MATCHUP", "")), None)
                away_row = next((r for r in teams if " @ " in r.get("MATCHUP", "")), None)
                if not home_row or not away_row:
                    continue

                home_id = int(home_row["TEAM_ID"])
                away_id = int(away_row["TEAM_ID"])

                home_pts = float(home_row.get("PTS") or 0)
                away_pts = float(away_row.get("PTS") or 0)
                actual_total = home_pts + away_pts
                if actual_total == 0:
                    continue

                try:
                    proj_total = float(calculate_projected_total(home_id, away_id))
                except Exception as ex:
                    errors.append({"game_id": str(game_id), "error": f"proj_total: {ex}"})
                    continue

                correct = actual_total >= proj_total
                try:
                    supabase_service.save_points_result(
                        game_id=str(game_id),
                        game_date=date_str,
                        projected_total=proj_total,
                        actual_total=actual_total,
                        correct=correct,
                    )
                    submitted.append({"game_id": str(game_id), "actual": actual_total, "projected": proj_total, "correct": correct})
                except Exception as ex:
                    errors.append({"game_id": str(game_id), "error": f"save: {ex}"})

        return {"synced": len(submitted), "results": submitted, "errors": errors, **supabase_service.get_points_record()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
