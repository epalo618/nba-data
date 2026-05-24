import math
import numpy as np
from typing import Optional
from app.services import nba_service


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


def calculate_win_probability(
    home_team_id: int,
    away_team_id: int,
    home_name: str = "Home",
    away_name: str = "Away",
) -> dict:
    adv_stats = nba_service.get_team_advanced_stats()
    adv = {r["TEAM_ID"]: r for r in adv_stats}

    home_adv = adv.get(home_team_id, {})
    away_adv = adv.get(away_team_id, {})

    home_net = float(home_adv.get("NET_RATING", 0) or 0)
    away_net = float(away_adv.get("NET_RATING", 0) or 0)
    home_ortg = float(home_adv.get("OFF_RATING", 110) or 110)
    home_drtg = float(home_adv.get("DEF_RATING", 110) or 110)
    away_ortg = float(away_adv.get("OFF_RATING", 110) or 110)
    away_drtg = float(away_adv.get("DEF_RATING", 110) or 110)

    # Recent form: average point differential over last 10 games
    home_games = nba_service.get_team_last_n_games(home_team_id, 10)
    away_games = nba_service.get_team_last_n_games(away_team_id, 10)

    def recent_net_rating(games: list) -> float:
        diffs = [g.get("PTS", 0) - g.get("PTS_ALLOWED", 0) for g in games]
        return sum(diffs) / len(diffs) if diffs else 0.0

    home_recent = recent_net_rating(home_games)
    away_recent = recent_net_rating(away_games)

    # Blend season net rating (65%) with recent form (35%)
    home_adj = 0.65 * home_net + 0.35 * home_recent
    away_adj = 0.65 * away_net + 0.35 * away_recent

    # Project spread: net rating diff + home court (empirical NBA average: +2.5 pts)
    HOME_COURT = 2.5
    spread = (home_adj - away_adj) + HOME_COURT

    # Convert spread to win probability via normal CDF
    # NBA game-to-game std dev ≈ 11 pts (empirically established)
    NBA_STD = 11.0
    home_prob = _norm_cdf(spread / NBA_STD)
    away_prob = 1 - home_prob

    favored = home_name if home_prob >= 0.5 else away_name
    underdog = away_name if home_prob >= 0.5 else home_name
    fav_net = home_net if home_prob >= 0.5 else away_net
    dog_net = away_net if home_prob >= 0.5 else home_net
    fav_recent = home_recent if home_prob >= 0.5 else away_recent
    dog_recent = away_recent if home_prob >= 0.5 else home_recent
    fav_ortg = home_ortg if home_prob >= 0.5 else away_ortg
    fav_drtg = home_drtg if home_prob >= 0.5 else away_drtg
    dog_ortg = away_ortg if home_prob >= 0.5 else home_ortg
    dog_drtg = away_drtg if home_prob >= 0.5 else home_drtg

    reasons = []

    net_gap = abs(fav_net - dog_net)
    if net_gap >= 6:
        reasons.append(
            f"{favored} has a {net_gap:.1f} pt/100 net rating edge ({fav_net:+.1f} vs {dog_net:+.1f}) — a dominant season-long advantage."
        )
    elif net_gap >= 2.5:
        reasons.append(
            f"{favored}'s net rating ({fav_net:+.1f}) meaningfully outpaces {underdog}'s ({dog_net:+.1f}) over a full season."
        )

    recent_gap = fav_recent - dog_recent
    if recent_gap >= 4:
        reasons.append(
            f"{favored} has been outscoring opponents by {fav_recent:+.1f} pts/game recently vs {underdog}'s {dog_recent:+.1f} — strong recent form."
        )
    elif recent_gap <= -4:
        reasons.append(
            f"{underdog} has better recent form ({dog_recent:+.1f} pt diff L10) but {favored}'s season-long efficiency still projects a win."
        )

    off_adv = fav_ortg - dog_drtg
    if off_adv >= 4:
        reasons.append(
            f"{favored}'s offense ({fav_ortg:.1f} ORtg) vs {underdog}'s defense ({dog_drtg:.1f} DRtg) is a {off_adv:.1f} pt mismatch."
        )
    elif dog_ortg - fav_drtg <= -3:
        reasons.append(
            f"{favored}'s defense ({fav_drtg:.1f} DRtg) significantly limits {underdog}'s offense ({dog_ortg:.1f} ORtg)."
        )

    if home_prob >= 0.5:
        reasons.append(f"{favored} has home court (+2.5 pts on average).")
    else:
        reasons.append(f"{favored}'s efficiency edge overcomes {home_name}'s home court advantage.")

    if not reasons:
        reasons.append(f"Close matchup — {favored} holds a slight edge based on net rating and recent form.")

    return {
        "home_win_prob": round(home_prob, 3),
        "away_win_prob": round(away_prob, 3),
        "favored_team": favored,
        "reasons": reasons,
        "factors": {
            "home_net_rating": round(home_net, 2),
            "away_net_rating": round(away_net, 2),
            "home_recent_net": round(home_recent, 2),
            "away_recent_net": round(away_recent, 2),
            "projected_spread": round(spread, 1),
        },
    }


def calculate_projected_total(home_team_id: int, away_team_id: int) -> float:
    adv_stats = nba_service.get_team_advanced_stats()
    adv = {r["TEAM_ID"]: r for r in adv_stats}

    home = adv.get(home_team_id, {})
    away = adv.get(away_team_id, {})

    # pace-adjusted projection: (home_off + away_off + home_def_allowed + away_def_allowed) / 2
    # using ortg and drtg
    home_ortg = home.get("OFF_RATING", 110)
    home_drtg = home.get("DEF_RATING", 110)
    away_ortg = away.get("OFF_RATING", 110)
    away_drtg = away.get("DEF_RATING", 110)
    home_pace = home.get("PACE", 100)
    away_pace = away.get("PACE", 100)
    avg_pace = (home_pace + away_pace) / 2

    # Expected points each team scores
    home_proj_pts = ((home_ortg + away_drtg) / 2) * (avg_pace / 100)
    away_proj_pts = ((away_ortg + home_drtg) / 2) * (avg_pace / 100)

    return round(home_proj_pts + away_proj_pts, 1)


def _decay_avg(games: list, col: str, scale: float = 1, decay: float = 0.85) -> float | None:
    """Exponential decay weighted average. Index 0 (most recent game) gets highest weight."""
    vals = [(g.get(col, 0) or 0) * scale for g in games if g.get(col) is not None]
    if not vals:
        return None
    weights = np.array([decay ** i for i in range(len(vals))])
    weights = weights / weights.sum()
    return round(float(np.dot(vals, weights)), 1)


def project_player_stats(player_id: int, opponent_team_id: int, stat_cols: list[str]) -> list[dict]:
    all_players = nba_service.get_player_season_stats()
    player_map = {p["PLAYER_ID"]: p for p in all_players}
    player = player_map.get(player_id)
    if not player:
        return []

    recent_games = nba_service.get_player_last_n_games(player_id, 10)
    last5 = recent_games[:5]
    last10 = recent_games[:10]

    # Stat-specific opponent defensive ranks (rank 1 = worst defense = easiest matchup)
    try:
        opp_ranks = nba_service.get_opponent_stat_ranks().get(int(opponent_team_id), {})
    except Exception:
        opp_ranks = {}

    # Playoff sample size — scale playoff weight by games played (full weight at 10+)
    playoff_gp = int(player.get("PLAYOFF_GP", 0))
    playoff_scale = min(playoff_gp / 10, 1.0)

    results = []
    stat_map = {"PTS": "PTS", "REB": "REB", "AST": "AST", "STL": "STL", "BLK": "BLK", "FG3M": "FG3M"}

    for stat in stat_cols:
        col = stat_map.get(stat, stat)
        season_avg = float((player.get(col, 0) or 0))

        raw_reg = player.get(f"{col}_REG")
        raw_playoff = player.get(f"{col}_PLAYOFF")
        reg_avg = float(round(raw_reg or 0, 1)) if raw_reg is not None else round(season_avg, 1)
        playoff_avg = float(round(raw_playoff or 0, 1)) if raw_playoff is not None else None

        l5 = _decay_avg(last5, col) or season_avg
        l10 = _decay_avg(last10, col) or season_avg

        # Stat-specific opponent factor: rank 1 → +0.15, rank 16 → 0, rank 30 → -0.14
        opp_rank = int(opp_ranks.get(stat, 15))
        opp_factor = (16 - opp_rank) / 100

        if playoff_avg is not None:
            # Redistribute unused playoff weight to L10 (60%) and season avg (40%)
            p_weight = 0.20 * playoff_scale
            extra = 0.20 * (1 - playoff_scale)
            base = (
                (0.35 + extra * 0.60) * l10
                + (0.25 + extra * 0.40) * season_avg
                + p_weight * playoff_avg
                + 0.15 * l5
                + 0.05 * reg_avg
            )
        else:
            base = 0.40 * season_avg + 0.35 * l10 + 0.15 * l5 + 0.10 * season_avg

        projection = int(round(base * (1 + opp_factor)))

        results.append({
            "player_id": int(player_id),
            "player_name": str(player.get("PLAYER_NAME", "")),
            "team_abbreviation": str(player.get("TEAM_ABBREVIATION", "")),
            "stat": stat,
            "season_avg": float(round(season_avg, 1)),
            "reg_season_avg": float(reg_avg),
            "playoff_avg": float(playoff_avg) if playoff_avg is not None else None,
            "last5_avg": float(l5),
            "last10_avg": float(l10),
            "opponent_rank": opp_rank,
            "projection": projection,
        })

    return results


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
