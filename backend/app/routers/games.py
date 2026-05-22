from fastapi import APIRouter, HTTPException
from app.services import nba_service, odds_service
from app.services.predictions_service import calculate_win_probability, calculate_projected_total

router = APIRouter()


@router.get("/today")
async def get_todays_games():
    try:
        data = nba_service.get_todays_games()
        games = data["games"]
        line_score = data["line_score"]

        # Fetch odds
        raw_odds = await odds_service.get_nba_odds()
        odds_map = odds_service.parse_odds(raw_odds)

        # Get team stats for name lookup
        all_teams = {t["id"]: t for t in nba_service.get_all_teams()}

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

            try:
                win_probs = calculate_win_probability(home_id, away_id, home_name, away_name)
                proj_total = calculate_projected_total(home_id, away_id)
            except Exception:
                win_probs = {"home_win_prob": 0.5, "away_win_prob": 0.5, "favored_team": None, "reasons": [], "factors": {}}
                proj_total = 220.0

            # Match odds
            odds_key = f"{home_name}|{away_name}"
            game_odds = odds_map.get(odds_key, {})

            over_under_line = game_odds.get("total")
            ou_rec = None
            if over_under_line:
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
                "projected_total": proj_total,
                "over_under_line": over_under_line,
                "over_under_rec": ou_rec,
                "odds": game_odds,
            })

        return {"games": enriched, "line_score": line_score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{home_team_id}/vs/{away_team_id}")
async def get_matchup(home_team_id: int, away_team_id: int):
    try:
        all_teams = {t["id"]: t for t in nba_service.get_all_teams()}
        home_name = all_teams.get(home_team_id, {}).get("full_name", f"Team {home_team_id}")
        away_name = all_teams.get(away_team_id, {}).get("full_name", f"Team {away_team_id}")
        win_probs = calculate_win_probability(home_team_id, away_team_id, home_name, away_name)
        proj_total = calculate_projected_total(home_team_id, away_team_id)
        home_log = nba_service.get_team_last_n_games(home_team_id, 10)
        away_log = nba_service.get_team_last_n_games(away_team_id, 10)
        home_pts = [g.get("PTS", 0) for g in home_log]
        away_pts = [g.get("PTS", 0) for g in away_log]
        home_allowed = [g.get("PTS_ALLOWED", 0) for g in home_log]
        away_allowed = [g.get("PTS_ALLOWED", 0) for g in away_log]

        return {
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "win_probability": win_probs,
            "projected_total": proj_total,
            "home_last10": {"pts": home_pts, "pts_allowed": home_allowed, "games": home_log},
            "away_last10": {"pts": away_pts, "pts_allowed": away_allowed, "games": away_log},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
