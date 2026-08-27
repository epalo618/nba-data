from app.services import nba_service, nfl_service

SPORT_SERVICES = {
    "nba": nba_service,
    "nfl": nfl_service,
}

PREDICTIONS_SERVICES: dict = {}  # populated below, after predictions_service is defined (avoids circular import)


def _load_predictions_services():
    from app.services import predictions_service, nfl_predictions_service
    PREDICTIONS_SERVICES["nba"] = predictions_service
    PREDICTIONS_SERVICES["nfl"] = nfl_predictions_service


_load_predictions_services()

# The Odds API sport_key strings.
ODDS_SPORT_KEYS = {
    "nba": "basketball_nba",
    "nfl": "americanfootball_nfl",
}


def resolve_odds_sport_key(sport: str) -> str | None:
    return ODDS_SPORT_KEYS.get(sport)
