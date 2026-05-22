import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
ODDS_BASE_URL = "https://api.the-odds-api.com/v4"


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
