import math
import numpy as np


def _norm_cdf(x: float) -> float:
    """Standard normal CDF via math.erf — no scipy needed."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


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
