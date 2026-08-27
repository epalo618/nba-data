from fastapi import APIRouter, HTTPException, Depends
from app.dependencies import get_sport_service

router = APIRouter()


@router.get("/")
def get_players(service=Depends(get_sport_service)):
    return service.get_all_active_players()


@router.get("/stats")
def get_player_stats(team_id: int = None, service=Depends(get_sport_service)):
    stats = service.get_player_season_stats()
    if team_id:
        stats = [p for p in stats if p.get("TEAM_ID") == team_id]
    return stats


@router.get("/{player_id}/gamelog")
def get_player_gamelog(player_id: str, n: int = 10, service=Depends(get_sport_service)):
    try:
        return service.get_player_last_n_games(player_id, n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
