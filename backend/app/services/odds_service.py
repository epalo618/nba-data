import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"


BOOKMAKER_PRIORITY = ["fanduel", "draftkings", "betmgm"]

STAT_TO_MARKET = {
    "PTS": "player_points",
    "REB": "player_rebounds",
    "AST": "player_assists",
    "FG3M": "player_threes",
    "STL": "player_steals",
    "BLK": "player_blocks",
}

BOOKMAKER_DISPLAY = {
    "fanduel": "FanDuel",
    "draftkings": "DraftKings",
    "betmgm": "BetMGM",
}


async def get_nba_events() -> list[dict]:
    if not ODDS_API_KEY:
        return []
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ODDS_BASE_URL}/sports/basketball_nba/events",
            params={"apiKey": ODDS_API_KEY},
            timeout=10,
        )
        return resp.json() if resp.status_code == 200 else []


async def get_player_props(event_id: str) -> list[dict]:
    if not ODDS_API_KEY:
        return []
    markets = ",".join(STAT_TO_MARKET.values())
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ODDS_BASE_URL}/sports/basketball_nba/events/{event_id}/odds",
            params={
                "apiKey": ODDS_API_KEY,
                "regions": "us",
                "markets": markets,
                "oddsFormat": "american",
            },
            timeout=10,
        )
        return resp.json().get("bookmakers", []) if resp.status_code == 200 else []


def parse_player_props(bookmakers: list[dict]) -> dict:
    """Returns {player_name: {stat: {"line": float, "book": str}}}"""
    result: dict = {}
    for bm in bookmakers:
        book_key = bm.get("key", "")
        book_name = BOOKMAKER_DISPLAY.get(book_key, book_key)
        priority = BOOKMAKER_PRIORITY.index(book_key) if book_key in BOOKMAKER_PRIORITY else 99
        for market in bm.get("markets", []):
            stat = next((s for s, m in STAT_TO_MARKET.items() if m == market["key"]), None)
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


async def get_nba_odds() -> list[dict]:
    if not ODDS_API_KEY:
        return []
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{ODDS_BASE_URL}/sports/basketball_nba/odds",
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
