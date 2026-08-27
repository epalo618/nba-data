from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_sport_service

router = APIRouter()


@router.get("/")
def get_teams(service=Depends(get_sport_service)):
    return service.get_all_teams()


@router.get("/stats")
def get_team_stats(service=Depends(get_sport_service)):
    base = service.get_team_season_stats()
    adv = service.get_team_advanced_stats()
    adv_map = {r["TEAM_ID"]: r for r in adv}
    # Generic merge: whatever keys each sport's advanced-stats fn returns get added,
    # with base's own fields taking priority on any name collision.
    return [{**adv_map.get(t["TEAM_ID"], {}), **t} for t in base]


@router.get("/{team_id}/gamelog")
def get_team_gamelog(team_id: int, n: int = 10, service=Depends(get_sport_service)):
    try:
        return service.get_team_last_n_games(team_id, n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
