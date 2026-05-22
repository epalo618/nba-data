import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import teams, players, games, predictions, record

app = FastAPI(title="NBA Analytics API", version="1.0.0")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(players.router, prefix="/api/players", tags=["players"])
app.include_router(games.router, prefix="/api/games", tags=["games"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(record.router, prefix="/api/record", tags=["record"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/debug/games")
def debug_games():
    from app.services import nba_service
    return nba_service.get_todays_games()


@app.get("/api/debug/odds")
async def debug_odds():
    from app.services import odds_service
    events = await odds_service.get_nba_events()
    if not events:
        return {"error": "no events returned — check ODDS_API_KEY", "events": []}
    event = events[0]
    bookmakers = await odds_service.get_player_props(event["id"])
    props = odds_service.parse_player_props(bookmakers)
    return {"event": event.get("id"), "bookmaker_count": len(bookmakers), "sample_props": dict(list(props.items())[:3])}
