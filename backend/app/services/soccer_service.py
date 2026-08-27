import os
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from app.services.cache_utils import make_cache

load_dotenv()

FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
BASE_URL = "https://api.football-data.org/v4"

# football-data.org competition codes for the 6 competitions available on its
# free tier (Europa League and MLS are paid-tier only there — dropped for now).
COMPETITION_CODES = {
    "epl": "PL",
    "laliga": "PD",
    "seriea": "SA",
    "bundesliga": "BL1",
    "ligue1": "FL1",
    "ucl": "CL",
}
LEAGUE_NAMES = {
    "epl": "Premier League",
    "laliga": "La Liga",
    "seriea": "Serie A",
    "bundesliga": "Bundesliga",
    "ligue1": "Ligue 1",
    "ucl": "Champions League",
}
DEFAULT_LEAGUE = "epl"
ALL_LEAGUES = "all"

# Free tier is 10 requests/minute — cache aggressively (hours, not the 1hr NBA
# uses) since standings/fixtures don't need near-real-time freshness.
CACHE_TTL = 6 * 3600
_cached = make_cache(default_ttl=CACHE_TTL)


class FootballDataError(Exception):
    pass


def _get(path: str, params: dict | None = None) -> dict:
    """Raises on any failure (missing key, network error, non-200, rate limit)
    rather than swallowing it into {} — that {} would otherwise get cached by
    _cached() as if it were a legitimate empty result, silently wedging every
    caller into an empty state for the full 6h TTL instead of surfacing the
    real error and retrying next call."""
    if not FOOTBALL_DATA_API_KEY:
        raise FootballDataError("FOOTBALL_DATA_API_KEY is not set")
    resp = httpx.get(
        f"{BASE_URL}{path}",
        headers={"X-Auth-Token": FOOTBALL_DATA_API_KEY},
        params=params or {},
        timeout=15,
    )
    if resp.status_code != 200:
        raise FootballDataError(f"{path} -> HTTP {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def _code(league: str | None) -> str:
    return COMPETITION_CODES.get(league or DEFAULT_LEAGUE, COMPETITION_CODES[DEFAULT_LEAGUE])


def _leagues_for(league: str | None) -> list[str]:
    """Returns the list of league keys to aggregate over: every competition
    for "all", or just the one requested (defaulting to EPL)."""
    if league == ALL_LEAGUES:
        return list(COMPETITION_CODES.keys())
    return [league or DEFAULT_LEAGUE]


def get_all_teams(league: str | None = None):
    def fetch_one(lg: str):
        code = _code(lg)
        def fetch():
            data = _get(f"/competitions/{code}/teams")
            return [
                {"id": t["id"], "full_name": t["name"], "abbreviation": t.get("tla") or t["name"][:3].upper(),
                 "nickname": t.get("shortName", ""), "city": "", "state": "", "year_founded": None,
                 "LEAGUE": LEAGUE_NAMES[lg]}
                for t in data.get("teams", [])
            ]
        return _cached(f"teams_{code}", fetch)

    seen: dict = {}
    for lg in _leagues_for(league):
        for team in fetch_one(lg):
            seen.setdefault(team["id"], team)  # a team can appear in >1 competition (e.g. league + UCL) — keep first
    return list(seen.values())


def get_all_active_players(league: str | None = None):
    # No player-level data on football-data.org's free tier.
    return []


def get_player_season_stats(league: str | None = None):
    # No player-level data on football-data.org's free tier.
    return []


def get_team_season_stats(league: str | None = None):
    def fetch_one(lg: str):
        code = _code(lg)
        def fetch():
            data = _get(f"/competitions/{code}/standings")
            out = []
            for group in data.get("standings", []):
                if group.get("type") != "TOTAL":
                    continue
                for row in group.get("table", []):
                    gp = row.get("playedGames", 0)
                    out.append({
                        "TEAM_ID": row["team"]["id"],
                        "TEAM_NAME": row["team"]["name"],
                        "LEAGUE": LEAGUE_NAMES[lg],
                        "GP": gp, "W": row.get("won", 0), "D": row.get("draw", 0), "L": row.get("lost", 0),
                        "W_PCT": round(row.get("won", 0) / gp, 3) if gp else 0,
                        "PTS_TOTAL": row.get("points", 0),
                        "GF": row.get("goalsFor", 0), "GA": row.get("goalsAgainst", 0), "GD": row.get("goalDifference", 0),
                    })
            return out
        return _cached(f"standings_{code}", fetch)

    out = []
    for lg in _leagues_for(league):
        out.extend(fetch_one(lg))
    return out


def get_team_advanced_stats(league: str | None = None):
    """Goals-per-game rates, needed by the Poisson win-probability model.
    Uses different keys than NBA/NFL's advanced stats — the frontend's soccer
    column config reads these directly."""
    def fetch():
        out = []
        for row in get_team_season_stats(league=league):
            gp = row["GP"] or 1
            out.append({
                "TEAM_ID": row["TEAM_ID"],
                "GF_PER_GAME": round(row["GF"] / gp, 2),
                "GA_PER_GAME": round(row["GA"] / gp, 2),
                "PTS_PER_GAME": round(row["PTS_TOTAL"] / gp, 2) if row["GP"] else 0,
            })
        return out
    return fetch()


def get_opponent_stat_ranks(league: str | None = None) -> dict:
    """Rank 1 = concedes the most goals/game = weakest defense = easiest matchup."""
    def fetch():
        rows = sorted(get_team_advanced_stats(league=league), key=lambda r: -r["GA_PER_GAME"])
        return {row["TEAM_ID"]: {"GOALS": i + 1} for i, row in enumerate(rows)}
    return _cached(f"opp_ranks_{league or DEFAULT_LEAGUE}", fetch, ttl=CACHE_TTL)


def _parse_match(m: dict, league_display: str | None = None) -> dict:
    home, away = m["homeTeam"], m["awayTeam"]
    played = m.get("status") == "FINISHED"
    row = {
        "GAME_ID": str(m["id"]),
        "GAME_STATUS_TEXT": m.get("status", "SCHEDULED").title(),
        "GAME_STATUS_ID": 3 if played else 1,
        "HOME_TEAM_ID": home.get("id"),
        "HOME_TEAM_CITY": "", "HOME_TEAM_NAME": home.get("name", "?"),
        "HOME_SCORE": (m.get("score", {}).get("fullTime", {}).get("home")) or 0,
        "VISITOR_TEAM_ID": away.get("id"),
        "VISITOR_TEAM_CITY": "", "VISITOR_TEAM_NAME": away.get("name", "?"),
        "VISITOR_SCORE": (m.get("score", {}).get("fullTime", {}).get("away")) or 0,
    }
    if league_display:
        row["LEAGUE"] = league_display
    return row


def get_games_for_date(date_str: str, league: str | None = None) -> dict:
    def fetch_one(lg: str):
        code = _code(lg)
        def fetch():
            data = _get(f"/competitions/{code}/matches", params={"dateFrom": date_str, "dateTo": date_str})
            return [_parse_match(m, LEAGUE_NAMES[lg]) for m in data.get("matches", [])]
        return _cached(f"games_{code}_{date_str}", fetch, ttl=1800)

    games = []
    for lg in _leagues_for(league):
        games.extend(fetch_one(lg))
    return {"games": games, "line_score": []}


def get_todays_games(league: str | None = None):
    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    return get_games_for_date(today, league=league)


def get_team_last_n_games(team_id: int, n: int = 10, league: str | None = None):
    # "all" (and any team playing in a cup alongside its domestic league) both
    # want matches across every competition that team plays in, so omit the
    # competitions filter rather than trying to guess which single league the
    # team "belongs to".
    code = None if league == ALL_LEAGUES else _code(league)
    def fetch():
        params = {"status": "FINISHED", "limit": n}
        if code:
            params["competitions"] = code
        data = _get(f"/teams/{team_id}/matches", params=params)
        out = []
        for m in data.get("matches", []):
            is_home = m["homeTeam"].get("id") == team_id
            ft = m.get("score", {}).get("fullTime", {})
            scored = ft.get("home") if is_home else ft.get("away")
            allowed = ft.get("away") if is_home else ft.get("home")
            out.append({"PTS": scored or 0, "PTS_ALLOWED": allowed or 0, "GAME_ID": str(m["id"])})
        return out
    return _cached(f"team_last_n_{team_id}_{code or 'all'}_{n}", fetch, ttl=3600)


def get_head_to_head(team_id: int, opp_team_id: int, league: str | None = None) -> dict:
    code = None if league == ALL_LEAGUES else _code(league)
    def fetch():
        # get_team_last_n_games's row shape doesn't carry opponent id, so fetch
        # match detail directly here rather than reusing (and duplicating) that call.
        params = {"status": "FINISHED", "limit": 20}
        if code:
            params["competitions"] = code
        data = _get(f"/teams/{team_id}/matches", params=params)
        wins = losses = 0
        for m in data.get("matches", []):
            opp = m["awayTeam"]["id"] if m["homeTeam"]["id"] == team_id else m["homeTeam"]["id"]
            if opp != opp_team_id:
                continue
            ft = m.get("score", {}).get("fullTime", {})
            is_home = m["homeTeam"]["id"] == team_id
            mine = ft.get("home") if is_home else ft.get("away")
            theirs = ft.get("away") if is_home else ft.get("home")
            if mine is None or theirs is None:
                continue
            if mine > theirs:
                wins += 1
            elif mine < theirs:
                losses += 1
        return {"team_wins": wins, "opp_wins": losses, "games_played": wins + losses}
    return _cached(f"h2h_{team_id}_{opp_team_id}_{code or 'all'}", fetch, ttl=6 * 3600)


def get_game_boxscore(game_id: str, league: str | None = None) -> list[dict]:
    return []


def get_team_game_results_for_date(date_str: str, league: str | None = None) -> list[dict]:
    """No player-prop tracker sync support for soccer yet (3-way outcomes need
    Phase 3's schema work) — returns [] so record.py's sync silently no-ops
    instead of crashing if ever invoked for soccer."""
    return []


def get_player_stats_for_date(date_str: str, league: str | None = None) -> list[dict]:
    return []
