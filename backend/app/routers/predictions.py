import json
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.services.predictions_service import (
    project_player_stats,
    get_prop_recommendation,
    calculate_win_probability,
    calculate_projected_total,
)
from app.services import nba_service
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def _numpy_default(obj):
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    return str(obj)

router = APIRouter()

PROP_STATS = ["PTS", "REB", "AST", "STL", "BLK", "FG3M"]


@router.get("/player/{player_id}/vs/{opponent_team_id}")
def get_player_projections(player_id: int, opponent_team_id: int):
    try:
        projections = project_player_stats(player_id, opponent_team_id, PROP_STATS)
        return projections
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/game/{home_team_id}/vs/{away_team_id}/players")
def get_game_player_projections(home_team_id: int, away_team_id: int, top_n: int = 8):
    try:
        all_player_stats = nba_service.get_player_season_stats()

        # Filter to players on each team, sorted by minutes
        home_players = sorted(
            [p for p in all_player_stats if p.get("TEAM_ID") == home_team_id],
            key=lambda x: x.get("MIN", 0),
            reverse=True,
        )[:top_n]

        away_players = sorted(
            [p for p in all_player_stats if p.get("TEAM_ID") == away_team_id],
            key=lambda x: x.get("MIN", 0),
            reverse=True,
        )[:top_n]

        home_projections = []
        for p in home_players:
            pid = p["PLAYER_ID"]
            projs = project_player_stats(pid, away_team_id, PROP_STATS, is_home=True)
            home_projections.append({
                "player_id": pid,
                "player_name": p["PLAYER_NAME"],
                "team_abbreviation": p["TEAM_ABBREVIATION"],
                "projections": projs,
            })

        away_projections = []
        for p in away_players:
            pid = p["PLAYER_ID"]
            projs = project_player_stats(pid, home_team_id, PROP_STATS, is_home=False)
            away_projections.append({
                "player_id": pid,
                "player_name": p["PLAYER_NAME"],
                "team_abbreviation": p["TEAM_ABBREVIATION"],
                "projections": projs,
            })

        return {
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "home_players": home_projections,
            "away_players": away_projections,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best-bets")
def get_best_bets():
    """Returns top prop bets ranked by projection vs combined season avg gap."""
    try:
        data = nba_service.get_todays_games()
        games = data["games"]
        all_player_stats = nba_service.get_player_season_stats()

        best_bets = []
        for game in games:
            home_id = game.get("HOME_TEAM_ID")
            away_id = game.get("VISITOR_TEAM_ID")
            if not home_id or not away_id:
                continue

            for team_id, opp_id, is_home in [(home_id, away_id, True), (away_id, home_id, False)]:
                team_players = sorted(
                    [p for p in all_player_stats if p.get("TEAM_ID") == team_id],
                    key=lambda x: x.get("MIN", 0),
                    reverse=True,
                )[:6]

                for p in team_players:
                    try:
                        projs = project_player_stats(p["PLAYER_ID"], opp_id, ["PTS", "REB", "AST", "FG3M", "STL", "BLK"], is_home=is_home)
                    except Exception:
                        continue
                    for proj in projs:
                        baseline = proj["season_avg"]  # blended reg + playoff avg
                        gap = abs(proj["projection"] - baseline)
                        if gap / max(baseline, 0.1) < 0.12:
                            continue
                        proj["gap"] = round(gap, 2)
                        proj["game"] = f"{game.get('HOME_TEAM_CITY', '')} vs {game.get('VISITOR_TEAM_CITY', '')}"
                        best_bets.append(proj)

        # Pick the single best prop per category, then rank by gap
        from collections import defaultdict
        by_stat: dict = defaultdict(list)
        for bet in best_bets:
            by_stat[bet["stat"]].append(bet)

        stat_order = ["PTS", "REB", "AST", "FG3M", "BLK", "STL"]
        best_per_stat = []
        for stat in stat_order:
            group = sorted(by_stat.get(stat, []), key=lambda x: -x["gap"])
            if group:
                best_per_stat.append(group[0])

        # Sort the best-per-category list by gap so strongest signal shows first
        best_per_stat.sort(key=lambda x: -x["gap"])
        return best_per_stat
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/yesterday")
def get_yesterday_results():
    """Returns yesterday's player prop projections vs actual stats."""
    try:
        eastern = ZoneInfo("America/New_York")
        yesterday = (datetime.now(eastern) - timedelta(days=1)).strftime("%Y-%m-%d")

        # Single API call for all player stats on that date
        player_game_rows = nba_service.get_player_stats_for_date(yesterday)
        if not player_game_rows:
            return []

        # Build game metadata map from yesterday's scoreboard
        data = nba_service.get_games_for_date(yesterday)
        game_meta: dict = {}
        for g in data.get("games", []):
            gid = g.get("GAME_ID")
            if gid:
                game_meta[gid] = {
                    "home_id": g.get("HOME_TEAM_ID"),
                    "away_id": g.get("VISITOR_TEAM_ID"),
                    "label": f"{g.get('VISITOR_TEAM_CITY', '')} @ {g.get('HOME_TEAM_CITY', '')}",
                }

        # Group player rows by game
        from collections import defaultdict
        by_game: dict = defaultdict(list)
        for row in player_game_rows:
            gid = row.get("GAME_ID")
            if gid:
                by_game[gid].append(row)

        results = []
        for game_id, rows in by_game.items():
            meta = game_meta.get(game_id, {})
            home_id = meta.get("home_id")
            away_id = meta.get("away_id")
            game_label = meta.get("label", game_id)

            for player_row in rows:
                pid = player_row.get("PLAYER_ID")
                if not pid:
                    continue

                # Skip players with under 10 minutes
                min_raw = player_row.get("MIN") or "0"
                try:
                    mins = float(str(min_raw).split(":")[0])
                except Exception:
                    mins = 0
                if mins < 10:
                    continue

                team_id = player_row.get("TEAM_ID")
                is_home = team_id == home_id
                opp_id = away_id if is_home else home_id
                if not opp_id:
                    continue

                try:
                    projs = project_player_stats(pid, opp_id, PROP_STATS, is_home=is_home)
                except Exception:
                    continue

                for proj in projs:
                    stat = proj["stat"]
                    actual_val = player_row.get(stat)
                    if actual_val is None:
                        continue
                    try:
                        actual_val = float(actual_val)
                    except Exception:
                        continue

                    season_avg = float(proj["season_avg"])
                    projection = int(proj["projection"])
                    predicted_over = bool(projection >= season_avg)
                    went_over = bool(actual_val >= season_avg)
                    correct = bool(predicted_over == went_over)

                    results.append({
                        "game": game_label,
                        "player_name": proj["player_name"],
                        "team_abbreviation": proj["team_abbreviation"],
                        "stat": stat,
                        "season_avg": season_avg,
                        "projection": projection,
                        "actual": actual_val,
                        "predicted_over": predicted_over,
                        "went_over": went_over,
                        "correct": correct,
                    })

        return Response(
            content=json.dumps(results, default=_numpy_default),
            media_type="application/json",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
