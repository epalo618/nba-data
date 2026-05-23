from fastapi import APIRouter, HTTPException
from app.services.predictions_service import (
    project_player_stats,
    get_prop_recommendation,
    calculate_win_probability,
    calculate_projected_total,
)
from app.services import nba_service
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

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
            projs = project_player_stats(pid, away_team_id, PROP_STATS)
            home_projections.append({
                "player_id": pid,
                "player_name": p["PLAYER_NAME"],
                "team_abbreviation": p["TEAM_ABBREVIATION"],
                "projections": projs,
            })

        away_projections = []
        for p in away_players:
            pid = p["PLAYER_ID"]
            projs = project_player_stats(pid, home_team_id, PROP_STATS)
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

            for team_id, opp_id in [(home_id, away_id), (away_id, home_id)]:
                team_players = sorted(
                    [p for p in all_player_stats if p.get("TEAM_ID") == team_id],
                    key=lambda x: x.get("MIN", 0),
                    reverse=True,
                )[:6]

                for p in team_players:
                    try:
                        projs = project_player_stats(p["PLAYER_ID"], opp_id, ["PTS", "REB", "AST", "FG3M", "STL", "BLK"])
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

        data = nba_service.get_games_for_date(yesterday)
        games = [g for g in data.get("games", []) if g.get("GAME_STATUS_ID") == 3]

        all_player_stats = nba_service.get_player_season_stats()
        player_season_map = {p["PLAYER_ID"]: p for p in all_player_stats}

        results = []
        for game in games:
            home_id = game.get("HOME_TEAM_ID")
            away_id = game.get("VISITOR_TEAM_ID")
            game_id = game.get("GAME_ID")
            if not home_id or not away_id or not game_id:
                continue

            game_label = f"{game.get('VISITOR_TEAM_CITY', '')} @ {game.get('HOME_TEAM_CITY', '')}"

            try:
                boxscore = nba_service.get_game_boxscore(game_id)
            except Exception:
                continue

            for player_row in boxscore:
                pid = player_row.get("PLAYER_ID")
                if not pid or pid not in player_season_map:
                    continue

                # Parse minutes — skip players with under 10 mins
                min_raw = player_row.get("MIN") or "0"
                try:
                    mins = float(str(min_raw).split(":")[0])
                except Exception:
                    mins = 0
                if mins < 10:
                    continue

                team_id = player_row.get("TEAM_ID")
                opp_id = away_id if team_id == home_id else home_id

                try:
                    projs = project_player_stats(pid, opp_id, PROP_STATS)
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

                    season_avg = proj["season_avg"]
                    projection = proj["projection"]
                    predicted_over = projection >= season_avg
                    went_over = actual_val >= season_avg
                    correct = predicted_over == went_over

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

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
