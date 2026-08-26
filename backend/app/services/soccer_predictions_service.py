import math
from app.services import soccer_service

# Starting estimate — soccer home advantage is commonly modeled in this range
# in public analytics writing. Backtest against real results and adjust (Phase 8).
HOME_ADV_FACTOR = 1.3

# Fallback league-average goals/game prior, used only when a league has too
# little data yet (e.g. matchday 1) to compute a real average from standings.
DEFAULT_LEAGUE_AVG_GOALS = 1.35

# "Virtual games" of league-average evidence blended into each team's observed
# goals-for/against rate (Bayesian-style shrinkage). Without this, a team that's
# conceded exactly 0 goals through 1-2 games (common and mostly luck this early
# in a season) makes its defense-strength term literally 0, which zeroes out the
# opponent's entire expected-goals in the Poisson model below — this constant
# keeps early-season small samples from producing degenerate predictions.
PRIOR_GAMES = 4

_MAX_GOALS = 8  # truncate the scoreline matrix at 0..8 per side


def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def _league_avg_goals(league: str | None) -> float:
    rows = soccer_service.get_team_season_stats(league=league)
    total_goals = sum(r["GF"] for r in rows)
    total_games = sum(r["GP"] for r in rows)
    if total_games == 0:
        return DEFAULT_LEAGUE_AVG_GOALS
    return total_goals / total_games


def _team_rates(team_id: int, league: str | None) -> tuple[float, float]:
    """Returns (goals_for_per_game, goals_against_per_game), shrunk toward the
    league average by PRIOR_GAMES worth of "virtual games" so small samples
    (e.g. matchday 1) don't produce extreme attack/defense-strength values."""
    rows = {r["TEAM_ID"]: r for r in soccer_service.get_team_season_stats(league=league)}
    row = rows.get(team_id)
    avg = _league_avg_goals(league)
    if not row:
        return avg, avg
    gp = row["GP"]
    gf = (row["GF"] + PRIOR_GAMES * avg) / (gp + PRIOR_GAMES)
    ga = (row["GA"] + PRIOR_GAMES * avg) / (gp + PRIOR_GAMES)
    return gf, ga


def calculate_win_probability(
    home_team_id: int,
    away_team_id: int,
    home_name: str = "Home",
    away_name: str = "Away",
    league: str | None = None,
) -> dict:
    league_avg = _league_avg_goals(league)
    home_gf, home_ga = _team_rates(home_team_id, league)
    away_gf, away_ga = _team_rates(away_team_id, league)

    home_attack = home_gf / league_avg
    home_defense = home_ga / league_avg
    away_attack = away_gf / league_avg
    away_defense = away_ga / league_avg

    home_lambda = league_avg * home_attack * away_defense * HOME_ADV_FACTOR
    away_lambda = league_avg * away_attack * home_defense
    home_lambda = max(0.1, home_lambda)
    away_lambda = max(0.1, away_lambda)

    home_probs = [_poisson_pmf(i, home_lambda) for i in range(_MAX_GOALS + 1)]
    away_probs = [_poisson_pmf(j, away_lambda) for j in range(_MAX_GOALS + 1)]

    home_win = draw = away_win = 0.0
    for i in range(_MAX_GOALS + 1):
        for j in range(_MAX_GOALS + 1):
            p = home_probs[i] * away_probs[j]
            if i > j:
                home_win += p
            elif i == j:
                draw += p
            else:
                away_win += p
    # Renormalize — the truncated 0..8 grid misses a small tail of probability.
    total = home_win + draw + away_win
    if total > 0:
        home_win, draw, away_win = home_win / total, draw / total, away_win / total

    if home_win >= away_win and home_win >= draw:
        favored, fav_prob = home_name, home_win
    elif away_win >= draw:
        favored, fav_prob = away_name, away_win
    else:
        favored, fav_prob = None, draw

    reasons = []
    if favored:
        gap = abs(home_gf - away_gf) if favored == home_name else abs(away_gf - home_gf)
        if gap >= 0.5:
            reasons.append(f"{favored} averages more goals/game this season than its opponent ({home_gf:.2f} vs {away_gf:.2f}).")
        if favored == home_name:
            reasons.append(f"{home_name} has home advantage.")
    if draw >= 0.28:
        reasons.append("Closely matched attack/defense numbers make a draw a real possibility.")
    if not reasons:
        reasons.append("Closely matched teams — no strong statistical edge either way.")

    return {
        "home_win_prob": round(home_win, 3),
        "draw_prob": round(draw, 3),
        "away_win_prob": round(away_win, 3),
        "favored_team": favored,
        "reasons": reasons,
        "factors": {
            "home_goals_per_game": round(home_gf, 2),
            "away_goals_per_game": round(away_gf, 2),
            "projected_home_goals": round(home_lambda, 2),
            "projected_away_goals": round(away_lambda, 2),
        },
    }


def calculate_projected_total(home_team_id: int, away_team_id: int, league: str | None = None) -> float:
    league_avg = _league_avg_goals(league)
    home_gf, home_ga = _team_rates(home_team_id, league)
    away_gf, away_ga = _team_rates(away_team_id, league)
    home_lambda = league_avg * (home_gf / league_avg) * (away_ga / league_avg) * HOME_ADV_FACTOR
    away_lambda = league_avg * (away_gf / league_avg) * (home_ga / league_avg)
    return round(max(0.1, home_lambda) + max(0.1, away_lambda), 2)


def project_player_stats(player_id, opponent_team_id, stat_cols, is_home: bool = False, league: str | None = None) -> list[dict]:
    # No player-level data available on football-data.org's free tier.
    return []
