from fastapi import HTTPException
from app.services.sports_registry import SPORT_SERVICES, PREDICTIONS_SERVICES


def get_sport_service(sport: str):
    service = SPORT_SERVICES.get(sport)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Unknown sport: {sport}")
    return service


def get_predictions_service(sport: str):
    service = PREDICTIONS_SERVICES.get(sport)
    if service is None:
        raise HTTPException(status_code=404, detail=f"Unknown sport: {sport}")
    return service
