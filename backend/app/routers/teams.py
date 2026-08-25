from fastapi import APIRouter, HTTPException, Depends, Query
from app.dependencies import get_sport_service

router = APIRouter()


@router.get("/")
def get_teams(service=Depends(get_sport_service)):
    return service.get_all_teams()


@router.get("/stats")
def get_team_stats(service=Depends(get_sport_service), league: str | None = Query(None)):
    base = service.get_team_season_stats(league=league)
    adv = service.get_team_advanced_stats(league=league)
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
def get_team_gamelog(team_id: int, n: int = 10, service=Depends(get_sport_service), league: str | None = Query(None)):
    try:
        return service.get_team_last_n_games(team_id, n, league=league)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
