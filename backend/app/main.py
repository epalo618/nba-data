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
