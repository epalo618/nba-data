import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"

# The Odds API bills one request per game for player props, so cache aggressively.
_PROPS_TTL = 900          # 15 min per matchup's parsed prop lines
_EVENTS_TTL = 300         # 5 min for the events list (event-id lookup)
_props_cache: dict = {}
_events_cache: dict = {}


def _norm_name(n: str) -> str:
    """Loose player-name key: lowercase, letters/digits/spaces only."""
    return "".join(c for c in (n or "").lower() if c.isalnum() or c == " ").strip()


BOOKMAKER_PRIORITY = ["fanduel", "draftkings", "betmgm"]

STAT_TO_MARKET_NBA = {
    "PTS": "player_points",
    "REB": "player_rebounds",
    "AST": "player_assists",
    "FG3M": "player_threes",
    "STL": "player_steals",
    "BLK": "player_blocks",
}

# Verified against The Odds API's betting-markets docs (2026-08-25).
STAT_TO_MARKET_NFL = {
    "PASSING_YARDS": "player_pass_yds",
    "PASSING_TDS": "player_pass_tds",
    "PASSING_INTERCEPTIONS": "player_pass_interceptions",
    "RUSHING_YARDS": "player_rush_yds",
    "RUSHING_TDS": "player_rush_tds",
    "RECEIVING_YARDS": "player_reception_yds",
    "RECEIVING_TDS": "player_reception_tds",
    "RECEPTIONS": "player_receptions",
}

BOOKMAKER_DISPLAY = {
    "fanduel": "FanDuel",
    "draftkings": "DraftKings",
    "betmgm": "BetMGM",
}

# The Odds API's sport_key strings are "{sport}_{league/competition}" (e.g.
# "basketball_nba", "americanfootball_nfl") — dispatch the stat->market map off
# the leading segment so this generalizes to new sports without touching callers.
_STAT_TO_MARKET_BY_SPORT_PREFIX = {
    "basketball": STAT_TO_MARKET_NBA,
    "americanfootball": STAT_TO_MARKET_NFL,
}


def _stat_map_for_sport_key(sport_key: str | None) -> dict:
    prefix = (sport_key or "").split("_", 1)[0]
    return _STAT_TO_MARKET_BY_SPORT_PREFIX.get(prefix, STAT_TO_MARKET_NBA)


async def get_events(sport_key: str) -> list[dict]:
    if not ODDS_API_KEY or not sport_key:
        return []
    hit = _events_cache.get(sport_key)
    if hit and time.time() - hit["ts"] < _EVENTS_TTL:
        return hit["data"]
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ODDS_BASE_URL}/sports/{sport_key}/events",
            params={"apiKey": ODDS_API_KEY},
            timeout=10,
        )
        data = resp.json() if resp.status_code == 200 else []
    if not isinstance(data, list):
        data = []
    _events_cache[sport_key] = {"data": data, "ts": time.time()}
    return data


def _match_event(events: list[dict], home_name: str, away_name: str) -> dict | None:
    """Find the Odds API event for a matchup by team name (exact, then nickname)."""
    hn, an = (home_name or "").lower(), (away_name or "").lower()
    for e in events:
        eh, ea = (e.get("home_team") or "").lower(), (e.get("away_team") or "").lower()
        if eh == hn and ea == an:
            return e
    hnick = hn.split()[-1] if hn else ""
    anick = an.split()[-1] if an else ""
    for e in events:
        eh, ea = (e.get("home_team") or "").lower(), (e.get("away_team") or "").lower()
        if hnick and anick and hnick in eh and anick in ea:
            return e
    return None


async def get_matchup_player_props(sport_key: str, home_name: str, away_name: str) -> dict:
    """Parsed player-prop lines for one matchup, keyed by normalized player name:
    {norm_name: {STAT: {"line": float, "book": str}}}. Costs one Odds API request
    per matchup (plus the shared events list); both are cached."""
    if not ODDS_API_KEY or not sport_key:
        return {}
    ck = f"{sport_key}|{home_name}|{away_name}"
    hit = _props_cache.get(ck)
    if hit and time.time() - hit["ts"] < _PROPS_TTL:
        return hit["data"]

    result: dict = {}
    try:
        event = _match_event(await get_events(sport_key), home_name, away_name)
        if event and event.get("id"):
            bookmakers = await get_player_props(sport_key, event["id"])
            parsed = parse_player_props(bookmakers, sport_key)
            result = {_norm_name(name): stats for name, stats in parsed.items()}
    except Exception:
        result = {}

    _props_cache[ck] = {"data": result, "ts": time.time()}
    return result


async def get_player_props(sport_key: str, event_id: str) -> list[dict]:
    if not ODDS_API_KEY or not sport_key:
        return []
    markets = ",".join(_stat_map_for_sport_key(sport_key).values())
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ODDS_BASE_URL}/sports/{sport_key}/events/{event_id}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": markets,
                "oddsFormat": "american",
            },
            timeout=10,
        )
        return resp.json().get("bookmakers", []) if resp.status_code == 200 else []


def parse_player_props(bookmakers: list[dict], sport_key: str = "basketball_nba") -> dict:
    """Returns {player_name: {stat: {"line": float, "book": str}}}"""
    stat_map = _stat_map_for_sport_key(sport_key)
    result: dict = {}
    for bm in bookmakers:
        book_key = bm.get("key", "")
        book_name = BOOKMAKER_DISPLAY.get(book_key, book_key)
        priority = BOOKMAKER_PRIORITY.index(book_key) if book_key in BOOKMAKER_PRIORITY else 99
        for market in bm.get("markets", []):
            stat = next((s for s, m in stat_map.items() if m == market["key"]), None)
            if not stat:
                continue
            for outcome in market.get("outcomes", []):
                if outcome.get("name") != "Over":
                    continue
                player = outcome.get("description", "")
                line = outcome.get("point")
                if not player or line is None:
                    continue
                existing = result.get(player, {}).get(stat)
                if existing is None or priority < existing.get("priority", 99):
                    result.setdefault(player, {})[stat] = {
                        "line": line,
                        "book": book_name,
                        "priority": priority,
                    }
    # Strip priority from output
    for player in result:
        for stat in result[player]:
            result[player][stat].pop("priority", None)
    return result


async def get_odds(sport_key: str) -> list[dict]:
    if not ODDS_API_KEY or not sport_key:
        return []
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ODDS_BASE_URL}/sports/{sport_key}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": "h2h,totals,spreads",
                "oddsFormat": "american",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        return resp.json()


def parse_odds(raw_odds: list[dict]) -> dict:
    """Returns a dict keyed by (home_team, away_team) with h2h, total, spread."""
    parsed = {}
    for game in raw_odds:
        home = game.get("home_team", "")
        away = game.get("away_team", "")
        key = f"{home}|{away}"
        result = {"home_team": home, "away_team": away, "total": None, "spread": None, "h2h": None}
        for bm in game.get("bookmakers", []):
            if bm["key"] not in ("draftkings", "fanduel", "betmgm"):
                continue
            for market in bm.get("markets", []):
                if market["key"] == "totals" and result["total"] is None:
                    for o in market["outcomes"]:
                        if o["name"] == "Over":
                            result["total"] = o.get("point")
                if market["key"] == "h2h" and result["h2h"] is None:
                    result["h2h"] = {o["name"]: o["price"] for o in market["outcomes"]}
                if market["key"] == "spreads" and result["spread"] is None:
                    result["spread"] = {o["name"]: {"point": o.get("point"), "price": o["price"]} for o in market["outcomes"]}
        parsed[key] = result
    return parsed
