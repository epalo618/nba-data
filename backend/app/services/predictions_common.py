import math
import numpy as np


def _norm_cdf(x: float) -> float:
    """Standard normal CDF via math.erf — no scipy needed."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def data_confidence(games_played: int, ramp_games: int) -> float:
    """Weight (0..1) to place on a team's *own* current-season performance vs. an
    external anchor (the betting market). 0 games -> 0 (trust the market fully);
    ramps linearly to 1.0 once the team has `ramp_games` games on the books."""
    if games_played <= 0 or ramp_games <= 0:
        return 0.0
    return min(1.0, games_played / ramp_games)


def blend(model_value, anchor_value, weight: float):
    """Linear blend: weight*model + (1-weight)*anchor, tolerating either side
    being missing (None)."""
    if model_value is None:
        return anchor_value
    if anchor_value is None:
        return model_value
    return weight * model_value + (1 - weight) * anchor_value


PROP_COLD_MARKET_WEIGHT = 0.75
PROP_EDGE_THRESHOLD = 0.08  # min |proj - line| / line to call OVER/UNDER


def anchor_prop_to_line(model_projection: float, line, games_played: int, ramp_games: int):
    """Blend a model prop projection with the sportsbook line the same way game
    totals are handled: the line carries PROP_COLD_MARKET_WEIGHT at season start
    and fades to 0 as the player accumulates current-season games.

    Returns (final_projection, basis) where basis is 'market' | 'blend' | 'model'.
    """
    if line is None:
        return model_projection, "model"
    conf = data_confidence(games_played, ramp_games)
    mw = PROP_COLD_MARKET_WEIGHT * (1 - conf)
    final = mw * line + (1 - mw) * model_projection
    basis = "market" if conf <= 0 else ("model" if conf >= 1 else "blend")
    return final, basis


def prop_recommendation(final_projection: float, line) -> str | None:
    """OVER / UNDER only when the projection clears PROP_EDGE_THRESHOLD; otherwise
    None (no edge, no pick)."""
    if line is None:
        return None
    edge = (final_projection - line) / max(abs(line), 0.1)
    if edge >= PROP_EDGE_THRESHOLD:
        return "OVER"
    if edge <= -PROP_EDGE_THRESHOLD:
        return "UNDER"
    return None


def win_prob_from_spread(home_spread: float, std: float) -> float:
    """Convert a betting point spread into a home win probability. `home_spread`
    is the number next to the home team (negative = home favored), so a -3 line
    with std 13.5 -> norm_cdf(3/13.5) ~= 0.59. The market spread already prices
    in injuries, trades and the draft, which is exactly what we lack a box-score
    signal for early in a season."""
    if home_spread is None or not std:
        return 0.5
    return _norm_cdf(-home_spread / std)


def _confidence_label(pct: float) -> str:
    if pct >= 0.70:
        return "STRONG"
    elif pct >= 0.62:
        return "HIGH"
    elif pct >= 0.55:
        return "MED"
    return "LOW"


def _decay_avg(games: list, col: str, scale: float = 1, decay: float = 0.85) -> float | None:
    """Exponential decay weighted average. Index 0 (most recent game) gets highest weight."""
    vals = [(g.get(col, 0) or 0) * scale for g in games if g.get(col) is not None]
    if not vals:
        return None
    weights = np.array([decay ** i for i in range(len(vals))])
    weights = weights / weights.sum()
    return round(float(np.dot(vals, weights)), 1)


def get_prop_recommendation(projection: float, line: float) -> tuple[str, str]:
    diff_pct = (projection - line) / max(line, 0.1)
    if diff_pct > 0.06:
        rec = "OVER"
        conf = _confidence_label(0.5 + min(diff_pct * 2, 0.25))
    elif diff_pct < -0.06:
        rec = "UNDER"
        conf = _confidence_label(0.5 + min(abs(diff_pct) * 2, 0.25))
    else:
        rec = "LEAN"
        conf = "LOW"
    return rec, conf
