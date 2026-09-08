from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Depends
from app.services import odds_service
from app.services.sports_registry import resolve_odds_sport_key
from app.dependencies import get_sport_service, get_predictions_service

router = APIRouter()

EASTERN = ZoneInfo("America/New_York")


def _week_start(anchor: date) -> date:
    """Sunday on/before `anchor`. Python's weekday() is Mon=0..Sun=6."""
    return anchor - timedelta(days=(anchor.weekday() + 1) % 7)


def _market_from_odds(game_odds: dict, home_name: str) -> dict:
    """Pull the home-team point spread and game total out of a parsed odds row.
    These are the market's roster-/injury-/draft-adjusted view of the game."""
    spread = game_odds.get("spread") or {}
    home_spread = (spread.get(home_name) or {}).get("point")
    return {"home_spread": home_spread, "total": game_odds.get("total")}


def _enrich_games(games, service, predictions, odds_map, all_teams):
    """Attach win probabilities, projected totals, odds and H2H to raw game rows."""
    calculate_win_probability = predictions.calculate_win_probability
    calculate_projected_total = predictions.calculate_projected_total

    enriched = []
    for game in games:
        home_id = game.get("HOME_TEAM_ID")
        away_id = game.get("VISITOR_TEAM_ID")
        if not home_id or not away_id:
            continue

        home_info = all_teams.get(home_id, {})
        away_info = all_teams.get(away_id, {})
        home_name = home_info.get("full_name") or f"{game.get('HOME_TEAM_CITY', '')} {game.get('HOME_TEAM_NAME', '')}".strip()
        away_name = away_info.get("full_name") or f"{game.get('VISITOR_TEAM_CITY', '')} {game.get('VISITOR_TEAM_NAME', '')}".strip()

        odds_key = f"{home_name}|{away_name}"
        game_odds = odds_map.get(odds_key, {})
        market = _market_from_odds(game_odds, home_name)

        try:
            win_probs = calculate_win_probability(home_id, away_id, home_name, away_name, market=market)
            proj_total = calculate_projected_total(home_id, away_id, market=market)
        except Exception:
            win_probs = {"home_win_prob": 0.5, "away_win_prob": 0.5, "favored_team": None, "reasons": [], "factors": {"basis": "none"}}
            proj_total = None

        try:
            h2h = service.get_head_to_head(home_id, away_id)
        except Exception:
            h2h = {"team_wins": 0, "opp_wins": 0, "games_played": 0}

        over_under_line = game_odds.get("total")
        ou_rec = None
        if over_under_line and proj_total is not None:
            diff = proj_total - over_under_line
            ou_rec = "OVER" if diff > 3 else ("UNDER" if diff < -3 else "LEAN")

        enriched.append({
            **game,
            "home_team_name": home_name,
            "away_team_name": away_name,
            "home_win_prob": win_probs["home_win_prob"],
            "away_win_prob": win_probs["away_win_prob"],
            "favored_team": win_probs.get("favored_team"),
            "win_reasons": win_probs.get("reasons", []),
            "win_prob_factors": win_probs["factors"],
            "projection_basis": win_probs.get("factors", {}).get("basis", "model"),
            "projected_total": proj_total,
            "over_under_line": over_under_line,
            "over_under_rec": ou_rec,
            "odds": game_odds,
            "h2h_home_wins": h2h["team_wins"],
            "h2h_away_wins": h2h["opp_wins"],
            "h2h_games_played": h2h["games_played"],
        })
    return enriched


@router.get("/today")
async def get_todays_games(
    sport: str,
    service=Depends(get_sport_service),
    predictions=Depends(get_predictions_service),
):
    try:
        data = service.get_todays_games()
        sport_key = resolve_odds_sport_key(sport)
        raw_odds = await odds_service.get_odds(sport_key)
        odds_map = odds_service.parse_odds(raw_odds)
        all_teams = {t["id"]: t for t in service.get_all_teams()}

        enriched = _enrich_games(data["games"], service, predictions, odds_map, all_teams)
        return {"games": enriched, "line_score": data["line_score"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/week")
async def get_week_games(
    sport: str,
    start: str | None = None,
    offset: int = 0,
    service=Depends(get_sport_service),
    predictions=Depends(get_predictions_service),
):
    """All games for a Sunday–Saturday week, each enriched with win probability
    and projected total. `start` pins the week's Sunday (YYYY-MM-DD); otherwise
    `offset` counts weeks forward/back from the current one."""
    try:
        if start:
            week_start = datetime.strptime(start, "%Y-%m-%d").date()
        else:
            today = datetime.now(EASTERN).date()
            week_start = _week_start(today) + timedelta(weeks=offset)
        week_start = _week_start(week_start)
        week_end = week_start + timedelta(days=6)

        sport_key = resolve_odds_sport_key(sport)
        raw_odds = await odds_service.get_odds(sport_key)
        odds_map = odds_service.parse_odds(raw_odds)
        all_teams = {t["id"]: t for t in service.get_all_teams()}

        days = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            date_str = d.isoformat()
            try:
                data = service.get_games_for_date(date_str)
                games = _enrich_games(data["games"], service, predictions, odds_map, all_teams)
            except Exception:
                games = []
            days.append({"date": date_str, "games": games})

        total_games = sum(len(day["games"]) for day in days)
        return {
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
            "total_games": total_games,
            "days": days,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{home_team_id}/vs/{away_team_id}")
async def get_matchup(
    home_team_id: int,
    away_team_id: int,
    sport: str,
    service=Depends(get_sport_service),
    predictions=Depends(get_predictions_service),
):
    try:
        all_teams = {t["id"]: t for t in service.get_all_teams()}
        home_name = all_teams.get(home_team_id, {}).get("full_name", f"Team {home_team_id}")
        away_name = all_teams.get(away_team_id, {}).get("full_name", f"Team {away_team_id}")

        sport_key = resolve_odds_sport_key(sport)
        raw_odds = await odds_service.get_odds(sport_key)
        game_odds = odds_service.parse_odds(raw_odds).get(f"{home_name}|{away_name}", {})
        market = _market_from_odds(game_odds, home_name)

        win_probs = predictions.calculate_win_probability(home_team_id, away_team_id, home_name, away_name, market=market)
        proj_total = predictions.calculate_projected_total(home_team_id, away_team_id, market=market)
        home_log = service.get_team_last_n_games(home_team_id, 10)
        away_log = service.get_team_last_n_games(away_team_id, 10)
        home_pts = [g.get("PTS", 0) for g in home_log]
        away_pts = [g.get("PTS", 0) for g in away_log]
        home_allowed = [g.get("PTS_ALLOWED", 0) for g in home_log]
        away_allowed = [g.get("PTS_ALLOWED", 0) for g in away_log]

        return {
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_team_name": home_name,
            "away_team_name": away_name,
            "win_probability": win_probs,
            "projected_total": proj_total,
            "home_last10": {"pts": home_pts, "pts_allowed": home_allowed, "games": home_log},
            "away_last10": {"pts": away_pts, "pts_allowed": away_allowed, "games": away_log},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
