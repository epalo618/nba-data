from app.services import nba_service, nfl_service, soccer_service

SPORT_SERVICES = {
    "nba": nba_service,
    "nfl": nfl_service,
    "soccer": soccer_service,
}

PREDICTIONS_SERVICES: dict = {}  # populated below, after predictions_service is defined (avoids circular import)


def _load_predictions_services():
    from app.services import predictions_service, nfl_predictions_service, soccer_predictions_service
    PREDICTIONS_SERVICES["nba"] = predictions_service
    PREDICTIONS_SERVICES["nfl"] = nfl_predictions_service
    PREDICTIONS_SERVICES["soccer"] = soccer_predictions_service


_load_predictions_services()

# The Odds API sport-key strings. NBA/NFL are plain strings; soccer is a dict of
# league -> sport_key since each competition is a separate "sport" to that API.
# Verified against The Odds API's docs (2026-08-25) — soccer's keys don't follow
# a uniform country-prefix pattern (e.g. "soccer_serie_a", not "soccer_italy_serie_a"),
# which the original placeholder values got wrong for 4 of these 8.
ODDS_SPORT_KEYS = {
    "nba": "basketball_nba",
    "nfl": "americanfootball_nfl",
    "soccer": {
        "epl": "soccer_epl",
        "laliga": "soccer_spain_la_liga",
        "seriea": "soccer_serie_a",
        "bundesliga": "soccer_bundesliga",
        "ligue1": "soccer_ligue_1",
        "ucl": "soccer_uefa_champs_league",
        "uel": "soccer_europa_league",
        "mls": "soccer_usa_mls",
    },
}

# Soccer runs on football-data.org (not API-Football — its free tier turned out
# to only serve seasons 2022-2024, no current-season data at all). Europa League
# and MLS aren't in football-data.org's free tier either, so only 6 competitions
# are live for now. Codes verified against the live API (2026-08-25).
SOCCER_LEAGUES = {
    "epl": {"name": "Premier League", "country": "England"},
    "laliga": {"name": "La Liga", "country": "Spain"},
    "seriea": {"name": "Serie A", "country": "Italy"},
    "bundesliga": {"name": "Bundesliga", "country": "Germany"},
    "ligue1": {"name": "Ligue 1", "country": "France"},
    "ucl": {"name": "Champions League", "country": "Europe"},
}


def resolve_odds_sport_key(sport: str, league: str | None = None) -> str | None:
    key = ODDS_SPORT_KEYS.get(sport)
    if isinstance(key, dict):
        return key.get(league) if league else None
    return key
