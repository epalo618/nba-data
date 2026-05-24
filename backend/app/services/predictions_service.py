import math
import numpy as np
from typing import Optional
from app.services import nba_service


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


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
    all_stats = nba_service.get_team_season_stats()
    adv_stats = nba_service.get_team_advanced_stats()

    base_stats = {r["TEAM_ID"]: r for r in all_stats}
    adv = {r["TEAM_ID"]: r for r in adv_stats}

    home = base_stats.get(home_team_id, {})
    away = base_stats.get(away_team_id, {})
    home_adv = adv.get(home_team_id, {})
    away_adv = adv.get(away_team_id, {})

    home_wp = home.get("W_PCT", 0.5)
    away_wp = away.get("W_PCT", 0.5)
    wp_diff = home_wp - away_wp

    home_net = home_adv.get("NET_RATING", 0)
    away_net = away_adv.get("NET_RATING", 0)
    net_diff = home_net - away_net

    home_ortg = home_adv.get("OFF_RATING", 110)
    home_drtg = home_adv.get("DEF_RATING", 110)
    away_ortg = away_adv.get("OFF_RATING", 110)
    away_drtg = away_adv.get("DEF_RATING", 110)

    home_pts = home.get("PTS", 0)
    away_pts = away.get("PTS", 0)

    home_games = nba_service.get_team_last_n_games(home_team_id, 10)
    away_games = nba_service.get_team_last_n_games(away_team_id, 10)
    home_recent_wins = sum(1 for g in home_games if g.get("WL") == "W")
    away_recent_wins = sum(1 for g in away_games if g.get("WL") == "W")
    home_recent_wp = home_recent_wins / max(len(home_games), 1)
    away_recent_wp = away_recent_wins / max(len(away_games), 1)
    form_diff = home_recent_wp - away_recent_wp

    home_court = 0.6

    score = (
        wp_diff * 1.5
        + net_diff * 0.08
        + form_diff * 0.8
        + home_court
    )

    home_prob = _sigmoid(score)
    away_prob = 1 - home_prob
    favored = home_name if home_prob >= 0.5 else away_name
    underdog = away_name if home_prob >= 0.5 else home_name
    fav_net = home_net if home_prob >= 0.5 else away_net
    dog_net = away_net if home_prob >= 0.5 else home_net
    fav_wp = home_wp if home_prob >= 0.5 else away_wp
    dog_wp = away_wp if home_prob >= 0.5 else home_wp
    fav_wins = home_recent_wins if home_prob >= 0.5 else away_recent_wins
    dog_wins = away_recent_wins if home_prob >= 0.5 else home_recent_wins
    fav_ortg = home_ortg if home_prob >= 0.5 else away_ortg
    fav_drtg = home_drtg if home_prob >= 0.5 else away_drtg
    dog_ortg = away_ortg if home_prob >= 0.5 else home_ortg
    dog_drtg = away_drtg if home_prob >= 0.5 else home_drtg
    fav_pts = home_pts if home_prob >= 0.5 else away_pts
    dog_pts = away_pts if home_prob >= 0.5 else home_pts

    reasons = []

    # Net rating reason
    net_gap = abs(fav_net - dog_net)
    if net_gap >= 10:
        reasons.append(
            f"{favored} has a dominant net rating of {fav_net:+.1f} vs {underdog}'s {dog_net:+.1f} "
            f"({net_gap:.1f} pt/100 possessions better on both ends)."
        )
    elif net_gap >= 4:
        reasons.append(
            f"{favored}'s net rating of {fav_net:+.1f} outpaces {underdog}'s {dog_net:+.1f} — "
            f"a meaningful {net_gap:.1f} pt/100 edge over a full season."
        )

    # Win percentage reason
    wp_gap = abs(fav_wp - dog_wp)
    if wp_gap >= 0.2:
        reasons.append(
            f"{favored} finished the regular season at {fav_wp:.1%} vs {underdog}'s {dog_wp:.1%} — "
            f"a {wp_gap:.1%} win rate gap that reflects sustained dominance."
        )
    elif wp_gap >= 0.08:
        reasons.append(
            f"{favored}'s {fav_wp:.1%} regular season win rate gives them a clear edge over "
            f"{underdog}'s {dog_wp:.1%}."
        )

    # Offense vs Defense matchup
    off_adv = fav_ortg - dog_drtg
    if off_adv >= 4:
        reasons.append(
            f"{favored}'s offense ({fav_ortg:.1f} ORtg) should feast against {underdog}'s defense "
            f"({dog_drtg:.1f} DRtg) — a {off_adv:.1f} pt mismatch."
        )
    def_adv = dog_ortg - fav_drtg
    if def_adv <= -3:
        reasons.append(
            f"{favored}'s defense ({fav_drtg:.1f} DRtg) is elite and will limit {underdog}'s "
            f"offense ({dog_ortg:.1f} ORtg) — a {abs(def_adv):.1f} pt suppression edge."
        )

    # Recent form reason — only mention if favored team actually has better recent record
    form_gap = fav_wins - dog_wins
    if form_gap >= 3:
        reasons.append(
            f"{favored} is playing better basketball lately, going {fav_wins}-{10 - fav_wins} "
            f"over their last 10 vs {underdog}'s {dog_wins}-{10 - dog_wins}."
        )
    elif form_gap >= 1 and fav_wins >= 6:
        reasons.append(
            f"Recent form favors {favored} ({fav_wins}-{10 - fav_wins} L10) "
            f"over {underdog} ({dog_wins}-{10 - dog_wins} L10)."
        )
    elif form_gap <= -3:
        reasons.append(
            f"{underdog} has better recent form ({dog_wins}-{10 - dog_wins} L10 vs {favored}'s "
            f"{fav_wins}-{10 - fav_wins}), but {favored}'s overall efficiency still projects a win."
        )

    # Scoring output
    pts_gap = abs(fav_pts - dog_pts)
    if pts_gap >= 5:
        reasons.append(
            f"{favored} averaged {fav_pts:.1f} PPG this season vs {underdog}'s {dog_pts:.1f} — "
            f"a {pts_gap:.1f} point scoring advantage."
        )

    # Home court
    if home_prob >= 0.5:
        reasons.append(f"{favored} has home court advantage tonight, worth ~3–4 pts historically.")
    else:
        reasons.append(
            f"Despite playing at {home_name}'s home court, {favored}'s edge in talent and efficiency "
            f"overcomes the home court boost."
        )

    if not reasons:
        reasons.append(f"This is a close matchup — {favored} holds a slight statistical edge.")

    return {
        "home_win_prob": round(home_prob, 3),
        "away_win_prob": round(away_prob, 3),
        "favored_team": favored,
        "reasons": reasons,
        "factors": {
            "win_pct_diff": round(wp_diff, 3),
            "net_rating_diff": round(net_diff, 2),
            "form_diff": round(form_diff, 3),
            "home_court_advantage": True,
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

        projection = float(round(base * (1 + opp_factor), 1))

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
