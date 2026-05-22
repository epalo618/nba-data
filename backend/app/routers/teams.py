from fastapi import APIRouter, HTTPException
from app.services import nba_service

router = APIRouter()


@router.get("/")
def get_teams():
    return nba_service.get_all_teams()


@router.get("/stats")
def get_team_stats():
    base = nba_service.get_team_season_stats()
    adv = nba_service.get_team_advanced_stats()
    adv_map = {r["TEAM_ID"]: r for r in adv}
    merged = []
    for t in base:
        tid = t["TEAM_ID"]
        a = adv_map.get(tid, {})
        merged.append({
            **t,
            "OFF_RATING": a.get("OFF_RATING"),
            "DEF_RATING": a.get("DEF_RATING"),
            "NET_RATING": a.get("NET_RATING"),
            "PACE": a.get("PACE"),
            "TS_PCT": a.get("TS_PCT"),
        })
    return merged


@router.get("/{team_id}/gamelog")
def get_team_gamelog(team_id: int, n: int = 10):
    try:
        return nba_service.get_team_last_n_games(team_id, n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
