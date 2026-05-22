from fastapi import APIRouter, HTTPException
from app.services.predictions_service import (
    project_player_stats,
    get_prop_recommendation,
    calculate_win_probability,
    calculate_projected_total,
)
from app.services import nba_service

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
    """Returns top prop bets of the day based on projection vs sportsbook line gap."""
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
                    projs = project_player_stats(p["PLAYER_ID"], opp_id, ["PTS", "REB", "AST", "FG3M"])
                    for proj in projs:
                        proj["game"] = f"{game.get('HOME_TEAM_CITY', '')} vs {game.get('VISITOR_TEAM_CITY', '')}"
                        best_bets.append(proj)

        # Sort within each stat category by divergence from season avg
        best_bets.sort(key=lambda x: (x["stat"], -abs(x["projection"] - x["season_avg"])))
        return best_bets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
