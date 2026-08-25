from app.services import nba_service

# Populated with real modules in later phases (NFL in Phase 4, soccer in Phase 6).
SPORT_SERVICES = {
    "nba": nba_service,
}

PREDICTIONS_SERVICES: dict = {}  # populated below, after predictions_service is defined (avoids circular import)


def _load_predictions_services():
    from app.services import predictions_service
    PREDICTIONS_SERVICES["nba"] = predictions_service


_load_predictions_services()

# The Odds API sport-key strings. NBA/NFL are plain strings; soccer is a dict of
# league -> sport_key since each competition is a separate "sport" to that API.
ODDS_SPORT_KEYS = {
    "nba": "basketball_nba",
    "nfl": "americanfootball_nfl",
    "soccer": {
        "epl": "soccer_epl",
        "laliga": "soccer_spain_la_liga",
        "seriea": "soccer_italy_serie_a",
        "bundesliga": "soccer_germany_bundesliga",
        "ligue1": "soccer_france_ligue_one",
        "ucl": "soccer_uefa_champs_league",
        "uel": "soccer_uefa_europa_league",
        "mls": "soccer_usa_mls",
    },
}

# API-Football league IDs + display info. Unused until Phase 6 (soccer backend) —
# defined now so the registry shape is stable. Verify IDs against API-Football's
# live /leagues list before relying on them.
SOCCER_LEAGUES = {
    "epl": {"api_football_id": 39, "name": "Premier League", "country": "England"},
    "laliga": {"api_football_id": 140, "name": "La Liga", "country": "Spain"},
    "seriea": {"api_football_id": 135, "name": "Serie A", "country": "Italy"},
    "bundesliga": {"api_football_id": 78, "name": "Bundesliga", "country": "Germany"},
    "ligue1": {"api_football_id": 61, "name": "Ligue 1", "country": "France"},
    "ucl": {"api_football_id": 2, "name": "Champions League", "country": "Europe"},
    "uel": {"api_football_id": 3, "name": "Europa League", "country": "Europe"},
    "mls": {"api_football_id": 253, "name": "MLS", "country": "USA"},
}


def resolve_odds_sport_key(sport: str, league: str | None = None) -> str | None:
    key = ODDS_SPORT_KEYS.get(sport)
    if isinstance(key, dict):
        return key.get(league) if league else None
    return key
