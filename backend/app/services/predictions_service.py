from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from app.services import nba_service
from app.services.predictions_common import (
    _norm_cdf, _confidence_label, _decay_avg, get_prop_recommendation,
    data_confidence, win_prob_from_spread,
)

# NBA game-to-game scoring std dev ≈ 11 pts (empirically established).
NBA_STD = 11.0
HOME_COURT = 2.5

# Games of current-season results before the model fully trusts a team's own
# numbers over the betting line (which already reflects trades/draft/injuries).
DATA_RAMP_GAMES = 12


def _team_gp(row: dict) -> int:
    return int(row.get("GP", 0) or 0)


def calculate_win_probability(
    home_team_id: int,
    away_team_id: int,
    home_name: str = "Home",
    away_name: str = "Away",
    league: str | None = None,
    market: dict | None = None,
) -> dict:
    market = market or {}
    market_spread = market.get("home_spread")

    adv = {r["TEAM_ID"]: r for r in nba_service.get_team_advanced_stats()}
    home_adv = adv.get(home_team_id, {})
    away_adv = adv.get(away_team_id, {})
    conf = min(
        data_confidence(_team_gp(home_adv), DATA_RAMP_GAMES),
        data_confidence(_team_gp(away_adv), DATA_RAMP_GAMES),
    )

    if conf <= 0.0 and market_spread is None:
        return {
            "home_win_prob": 0.5,
            "away_win_prob": 0.5,
            "favored_team": None,
            "reasons": ["No 2026-27 results and no betting line yet — treated as a coin flip until data arrives."],
            "factors": {"data_confidence": 0.0, "basis": "none"},
        }

    home_net = float(home_adv.get("NET_RATING", 0) or 0)
    away_net = float(away_adv.get("NET_RATING", 0) or 0)
    home_ortg = float(home_adv.get("OFF_RATING", 110) or 110)
    home_drtg = float(home_adv.get("DEF_RATING", 110) or 110)
    away_ortg = float(away_adv.get("OFF_RATING", 110) or 110)
    away_drtg = float(away_adv.get("DEF_RATING", 110) or 110)

    def recent_net_rating(games: list) -> float:
        diffs = [g.get("PTS", 0) - g.get("PTS_ALLOWED", 0) for g in games]
        return sum(diffs) / len(diffs) if diffs else 0.0

    home_recent = recent_net_rating(nba_service.get_team_last_n_games(home_team_id, 10))
    away_recent = recent_net_rating(nba_service.get_team_last_n_games(away_team_id, 10))

    home_adj = 0.65 * home_net + 0.35 * home_recent
    away_adj = 0.65 * away_net + 0.35 * away_recent
    model_spread = (home_adj - away_adj) + HOME_COURT
    model_home_prob = _norm_cdf(model_spread / NBA_STD)

    market_home_prob = (
        win_prob_from_spread(market_spread, NBA_STD) if market_spread is not None else None
    )

    if market_home_prob is None:
        home_prob, basis = model_home_prob, "model"
    elif conf <= 0.0:
        home_prob, basis = market_home_prob, "market"
    else:
        home_prob = conf * model_home_prob + (1 - conf) * market_home_prob
        basis = "blend"

    home_prob = max(0.02, min(0.98, home_prob))
    away_prob = 1 - home_prob
    favored = home_name if home_prob >= 0.5 else away_name
    underdog = away_name if home_prob >= 0.5 else home_name
    fav_prob = max(home_prob, away_prob)

    reasons: list[str] = []
    if basis in ("market", "blend") and market_spread is not None:
        mag = abs(market_spread)
        if mag < 1:
            reasons.append(
                "Betting line has this as a pick'em — the market (which already reflects offseason trades, "
                "the draft, and injury news) sees two evenly matched teams."
            )
        else:
            reasons.append(
                f"Betting line: {favored} favored by {mag:.1f}. The market already accounts for offseason "
                f"roster moves and injuries; that implies about a {fav_prob:.0%} chance to win."
            )
    if basis == "blend":
        reasons.append(
            f"Weighted {conf:.0%} toward actual 2026-27 results and {1 - conf:.0%} toward the betting line; "
            f"the mix shifts to on-court results as more games are played."
        )
    if basis in ("model", "blend"):
        fav_net = home_net if favored == home_name else away_net
        dog_net = away_net if favored == home_name else home_net
        net_gap = abs(fav_net - dog_net)
        if net_gap >= 4:
            reasons.append(
                f"{favored}'s net rating ({fav_net:+.1f}) outpaces {underdog}'s ({dog_net:+.1f}) by "
                f"{net_gap:.1f} points per 100 possessions this season."
            )
        if favored == home_name:
            reasons.append(f"{favored} has home court (~{HOME_COURT:.1f} pts on average).")
    if not reasons:
        reasons.append(f"{favored} holds a slight edge in this matchup.")

    return {
        "home_win_prob": round(home_prob, 3),
        "away_win_prob": round(away_prob, 3),
        "favored_team": favored,
        "reasons": reasons,
        "factors": {
            "data_confidence": round(conf, 2),
            "basis": basis,
            "market_spread": market_spread,
            "model_spread": round(model_spread, 1),
            "home_net_rating": round(home_net, 2),
            "away_net_rating": round(away_net, 2),
        },
    }


def calculate_projected_total(
    home_team_id: int,
    away_team_id: int,
    league: str | None = None,
    market: dict | None = None,
) -> float | None:
    market = market or {}
    market_total = market.get("total")

    adv = {r["TEAM_ID"]: r for r in nba_service.get_team_advanced_stats()}
    home = adv.get(home_team_id, {})
    away = adv.get(away_team_id, {})
    conf = min(
        data_confidence(_team_gp(home), DATA_RAMP_GAMES),
        data_confidence(_team_gp(away), DATA_RAMP_GAMES),
    )

    if conf <= 0.0:
        return round(market_total, 1) if market_total is not None else None

    home_ortg = home.get("OFF_RATING", 110)
    home_drtg = home.get("DEF_RATING", 110)
    away_ortg = away.get("OFF_RATING", 110)
    away_drtg = away.get("DEF_RATING", 110)
    avg_pace = (home.get("PACE", 100) + away.get("PACE", 100)) / 2

    season_home = ((home_ortg + away_drtg) / 2) * (avg_pace / 100)
    season_away = ((away_ortg + home_drtg) / 2) * (avg_pace / 100)
    model_total = season_home + season_away

    try:
        home_games = nba_service.get_team_last_n_games(home_team_id, 8)
        away_games = nba_service.get_team_last_n_games(away_team_id, 8)

        def _avg(games, field):
            vals = [float(g[field]) for g in games if g.get(field) is not None]
            return sum(vals) / len(vals) if vals else None

        h_scored = _avg(home_games, "PTS")
        h_allowed = _avg(home_games, "PTS_ALLOWED")
        a_scored = _avg(away_games, "PTS")
        a_allowed = _avg(away_games, "PTS_ALLOWED")
        if all(v is not None for v in [h_scored, h_allowed, a_scored, a_allowed]):
            recent_proj = (h_scored + a_allowed) / 2 + (a_scored + h_allowed) / 2
            model_total = 0.6 * recent_proj + 0.4 * model_total
    except Exception:
        pass

    if market_total is None:
        return int(round(model_total))
    return round(conf * model_total + (1 - conf) * market_total, 1)


def _days_rest(recent_games: list) -> int:
    """Days of rest before the upcoming game (0 = back-to-back). Returns 3 if unknown."""
    if not recent_games:
        return 3
    raw = recent_games[0].get("GAME_DATE", "")
    if not raw:
        return 3
    try:
        last_date = datetime.strptime(str(raw).strip().title(), "%b %d, %Y").date()
        today = datetime.now(ZoneInfo("America/New_York")).date()
        return max(0, (today - last_date).days - 1)
    except Exception:
        return 3


def project_player_stats(player_id: int | str, opponent_team_id: int, stat_cols: list[str], is_home: bool = False, league: str | None = None) -> list[dict]:
    # player_id arrives as str from the route (NFL's GSIS ids aren't numeric), but
    # nba_api's PLAYER_ID is an int — cast up front so every lookup below matches.
    player_id = int(player_id)
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

        # Opponent factor capped at ±8% (rank 1 = worst defense = easiest matchup)
        opp_rank = int(opp_ranks.get(stat, 15))
        opp_factor = max(-0.08, min(0.08, (16 - opp_rank) / 100))

        if playoff_avg is not None:
            # Redistribute unused playoff weight to L10 (60%) and season avg (40%)
            p_weight = 0.20 * playoff_scale
            extra = 0.20 * (1 - playoff_scale)
            base = (
                (0.38 + extra * 0.60) * l10
                + (0.17 + extra * 0.40) * season_avg
                + p_weight * playoff_avg
                + 0.20 * l5
                + 0.05 * reg_avg
            )
        else:
            base = 0.30 * season_avg + 0.45 * l10 + 0.25 * l5

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
