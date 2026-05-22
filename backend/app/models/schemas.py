from pydantic import BaseModel
from typing import Optional


class TeamStats(BaseModel):
    team_id: int
    team_name: str
    abbreviation: str
    wins: int
    losses: int
    win_pct: float
    pts: float
    reb: float
    ast: float
    stl: float
    blk: float
    tov: float
    off_rating: float
    def_rating: float
    net_rating: float
    pace: float
    ts_pct: float


class PlayerStats(BaseModel):
    player_id: int
    player_name: str
    team_id: int
    team_abbreviation: str
    age: Optional[float]
    gp: int
    min: float
    pts: float
    reb: float
    ast: float
    stl: float
    blk: float
    tov: float
    fg_pct: float
    fg3_pct: float
    ft_pct: float
    plus_minus: float


class PlayerProjection(BaseModel):
    player_id: int
    player_name: str
    team_abbreviation: str
    stat: str
    season_avg: float
    last5_avg: float
    last10_avg: float
    vs_opponent_avg: float
    opponent_rank: int
    projection: float
    line: Optional[float]
    recommendation: Optional[str]
    confidence: Optional[str]


class GameMatchup(BaseModel):
    game_id: str
    home_team_id: int
    home_team_name: str
    home_team_abbr: str
    away_team_id: int
    away_team_name: str
    away_team_abbr: str
    game_date: str
    home_win_prob: float
    away_win_prob: float
    projected_total: float
    over_under_line: Optional[float]
    over_under_rec: Optional[str]


class WinProbability(BaseModel):
    home_team: str
    away_team: str
    home_win_prob: float
    away_win_prob: float
    factors: dict
