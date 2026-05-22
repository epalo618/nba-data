from fastapi import APIRouter, HTTPException
from app.services.predictions_service import (
    project_player_stats,
    get_prop_recommendation,
    calculate_win_probability,
    calculate_projected_total,
)
from app.services import nba_service, odds_service

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
async def get_best_bets():
    """Returns top prop bets of the day based on projection vs sportsbook line gap."""
    try:
        data = nba_service.get_todays_games()
        games = data["games"]
        all_player_stats = nba_service.get_player_season_stats()

        # Fetch player prop lines from odds API
        prop_lines: dict = {}
        events = await odds_service.get_nba_events()
        for event in events:
            bookmakers = await odds_service.get_player_props(event["id"])
            player_map = odds_service.parse_player_props(bookmakers)
            for player, stats in player_map.items():
                prop_lines.setdefault(player, {}).update(stats)

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
                    projs = project_player_stats(p["PLAYER_ID"], opp_id, ["PTS", "REB", "AST", "FG3M", "STL", "BLK"])
                    player_props = prop_lines.get(p.get("PLAYER_NAME", ""), {})
                    for proj in projs:
                        prop = player_props.get(proj["stat"], {})
                        line = prop.get("line")
                        if line is None:
                            continue
                        gap = abs(proj["projection"] - line)
                        if gap / max(line, 0.1) < 0.08:
                            continue
                        proj["line"] = line
                        proj["line_source"] = prop.get("book")
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
