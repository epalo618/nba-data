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
    # Keyed by (TEAM_ID, LEAGUE) rather than just TEAM_ID — under soccer's "all
    # leagues" mode a team can appear once per competition it plays in (e.g.
    # Arsenal in both Premier League and Champions League standings), and a
    # TEAM_ID-only key would let one competition's advanced stats silently
    # overwrite another's for the same club. LEAGUE is absent for NBA/NFL, so
    # this collapses back to a plain TEAM_ID key for them.
    adv_map = {(r["TEAM_ID"], r.get("LEAGUE")): r for r in adv}
    # Generic merge: whatever keys each sport's advanced-stats fn returns get added,
    # with base's own fields taking priority on any name collision.
    return [{**adv_map.get((t["TEAM_ID"], t.get("LEAGUE")), {}), **t} for t in base]


@router.get("/{team_id}/gamelog")
def get_team_gamelog(team_id: int, n: int = 10, service=Depends(get_sport_service), league: str | None = Query(None)):
    try:
        return service.get_team_last_n_games(team_id, n, league=league)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
