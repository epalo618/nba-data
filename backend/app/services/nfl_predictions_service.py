from app.services import nfl_service
from app.services.nfl_service import POSITION_STAT_COLS
from app.services.predictions_common import (
    _norm_cdf, _decay_avg, data_confidence, win_prob_from_spread,
)

# Starting estimates only — NFL public-analytics figures commonly cited in this
# range. Backtest against real tracker results (Phase 8) and adjust.
HOME_FIELD_NFL = 2.0
NFL_STD = 13.5

# Games of current-season results before the model fully trusts a team's own
# numbers over the betting line. Below this, projections lean on the market —
# which already reflects offseason trades, the draft, and injury news.
DATA_RAMP_GAMES = 4

# Game-total projection: at kickoff the market total gets COLD_MARKET_WEIGHT and
# the rest is an independent scoring model; the market share fades to 0 as a
# team's own current-season data accumulates. The model's own baseline is last
# season's combined scoring, regressed PRIOR_REGRESSION of the way toward the
# league-average total (scoring level carries over between seasons; specific
# results do not).
LEAGUE_AVG_TOTAL_NFL = 44.0
PRIOR_REGRESSION = 0.40
COLD_MARKET_WEIGHT = 0.75


def _scoring_total(home: dict, away: dict) -> float | None:
    """Expected combined points from two {PTS, PTS_ALLOWED} rows, or None if
    either side is missing its numbers."""
    hp, hpa = home.get("PTS"), home.get("PTS_ALLOWED")
    ap, apa = away.get("PTS"), away.get("PTS_ALLOWED")
    if None in (hp, hpa, ap, apa):
        return None
    return (hp + apa) / 2 + (ap + hpa) / 2


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
    market_spread = market.get("home_spread")  # points next to home team; negative = home favored

    season = {r["TEAM_ID"]: r for r in nfl_service.get_team_season_stats()}
    home_season = season.get(home_team_id, {})
    away_season = season.get(away_team_id, {})
    conf = min(
        data_confidence(_team_gp(home_season), DATA_RAMP_GAMES),
        data_confidence(_team_gp(away_season), DATA_RAMP_GAMES),
    )

    # Nothing to go on yet: no 2026 games and no betting line.
    if conf <= 0.0 and market_spread is None:
        return {
            "home_win_prob": 0.5,
            "away_win_prob": 0.5,
            "favored_team": None,
            "reasons": ["No 2026 results and no betting line yet — treated as a coin flip until data arrives."],
            "factors": {"data_confidence": 0.0, "basis": "none"},
        }

    # Model estimate from current-season scoring margin + recent form.
    home_net = home_season.get("PTS", 21) - home_season.get("PTS_ALLOWED", 21)
    away_net = away_season.get("PTS", 21) - away_season.get("PTS_ALLOWED", 21)

    def recent_diff(games: list) -> float:
        diffs = [g.get("PTS", 0) - g.get("PTS_ALLOWED", 0) for g in games]
        return sum(diffs) / len(diffs) if diffs else 0.0

    home_recent = recent_diff(nfl_service.get_team_last_n_games(home_team_id, 5))
    away_recent = recent_diff(nfl_service.get_team_last_n_games(away_team_id, 5))
    home_adj = 0.65 * home_net + 0.35 * home_recent
    away_adj = 0.65 * away_net + 0.35 * away_recent
    model_spread = (home_adj - away_adj) + HOME_FIELD_NFL  # home margin, + = home better
    model_home_prob = _norm_cdf(model_spread / NFL_STD)

    market_home_prob = (
        win_prob_from_spread(market_spread, NFL_STD) if market_spread is not None else None
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

    reasons = _win_reasons(
        basis, conf, favored, underdog, home_name, home_prob,
        market_spread, home_net, away_net,
    )

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
            "home_net": round(home_net, 2),
            "away_net": round(away_net, 2),
        },
    }


def _win_reasons(basis, conf, favored, underdog, home_name, home_prob,
                 market_spread, home_net, away_net) -> list[str]:
    fav_prob = max(home_prob, 1 - home_prob)
    reasons: list[str] = []

    if basis in ("market", "blend") and market_spread is not None:
        mag = abs(market_spread)
        if mag < 1:
            reasons.append(
                f"Betting line has this as a pick'em — the market (which already prices in offseason "
                f"trades, the draft, and injury news) sees two evenly matched teams."
            )
        else:
            reasons.append(
                f"Betting line: {favored} favored by {mag:.1f}. The market already accounts for offseason "
                f"roster moves and injuries; that implies about a {fav_prob:.0%} chance to win."
            )

    if basis == "blend":
        reasons.append(
            f"Weighted {conf:.0%} toward {favored}/{underdog}'s actual 2026 results so far and "
            f"{1 - conf:.0%} toward the betting line; the mix shifts to on-field results as more games are played."
        )

    if basis in ("model", "blend"):
        fav_net = home_net if favored == home_name else away_net
        dog_net = away_net if favored == home_name else home_net
        gap = abs(fav_net - dog_net)
        if gap >= 4:
            reasons.append(
                f"{favored}'s 2026 scoring margin ({fav_net:+.1f}/game) is {gap:.1f} points better than "
                f"{underdog}'s ({dog_net:+.1f})."
            )
        if favored == home_name:
            reasons.append(f"{favored} is home (~{HOME_FIELD_NFL:.1f} pts of edge on average).")

    if not reasons:
        reasons.append(f"{favored} holds a slight edge in this matchup.")
    return reasons


def calculate_projected_total(
    home_team_id: int,
    away_team_id: int,
    league: str | None = None,
    market: dict | None = None,
) -> float | None:
    market = market or {}
    market_total = market.get("total")

    season = {r["TEAM_ID"]: r for r in nfl_service.get_team_season_stats()}
    home = season.get(home_team_id)
    away = season.get(away_team_id)
    conf = min(
        data_confidence(_team_gp(home or {}), DATA_RAMP_GAMES),
        data_confidence(_team_gp(away or {}), DATA_RAMP_GAMES),
    )

    # Current-season scoring model (season stats blended with last-5 recent form).
    cur_total = None
    if home is not None and away is not None:
        cur_total = _scoring_total(home, away)
        try:
            def _avg(games, field):
                vals = [g[field] for g in games if g.get(field) is not None]
                return sum(vals) / len(vals) if vals else None

            hg = nfl_service.get_team_last_n_games(home_team_id, 5)
            ag = nfl_service.get_team_last_n_games(away_team_id, 5)
            hs, ha = _avg(hg, "PTS"), _avg(hg, "PTS_ALLOWED")
            as_, aa = _avg(ag, "PTS"), _avg(ag, "PTS_ALLOWED")
            if cur_total is not None and None not in (hs, ha, as_, aa):
                recent = (hs + aa) / 2 + (as_ + ha) / 2
                cur_total = 0.6 * recent + 0.4 * cur_total
        except Exception:
            pass

    # Prior-season combined scoring, regressed toward the league-average total.
    prior = nfl_service.get_prior_team_scoring()
    prior_raw = _scoring_total(prior.get(home_team_id, {}), prior.get(away_team_id, {}))
    prior_total = None
    if prior_raw is not None:
        prior_total = (1 - PRIOR_REGRESSION) * prior_raw + PRIOR_REGRESSION * LEAGUE_AVG_TOTAL_NFL

    # Model = ramp from the regressed prior toward current-season scoring.
    if cur_total is not None and prior_total is not None:
        model_total = conf * cur_total + (1 - conf) * prior_total
    else:
        model_total = cur_total if cur_total is not None else prior_total

    # Blend with the market: it carries COLD_MARKET_WEIGHT at kickoff, fading to 0.
    if market_total is None:
        combined = model_total
    elif model_total is None:
        combined = market_total
    else:
        mw = COLD_MARKET_WEIGHT * (1 - conf)
        combined = mw * market_total + (1 - mw) * model_total

    return round(combined) if combined is not None else None


def project_player_stats(player_id: str, opponent_team_id: int, stat_cols: list[str], is_home: bool = False, league: str | None = None) -> list[dict]:
    all_players = nfl_service.get_player_season_stats()
    player_map = {p["PLAYER_ID"]: p for p in all_players}
    player = player_map.get(player_id)
    if not player:
        return []

    # Position-specific stat categories override whatever generic stat_cols the
    # router passed in — NFL props are position-dependent (a QB has no rushing
    # peers), unlike NBA's fixed PTS/REB/AST/... list. Positions with no defined
    # categories here (K, DEF/IDP, OL, ...) have no NFL prop stats to project —
    # falling back to stat_cols (NBA-shaped) would emit bogus all-zero PTS/REB/
    # etc. rows, so return nothing for them instead.
    position = player.get("POSITION", "")
    actual_stats = POSITION_STAT_COLS.get(position)
    if not actual_stats:
        return []

    recent_games = nfl_service.get_player_last_n_games(player_id, 5)
    opp_ranks = nfl_service.get_opponent_stat_ranks().get(opponent_team_id, {})

    results = []
    for stat in actual_stats:
        season_avg = float(player.get(stat, 0) or 0)
        decayed = _decay_avg(recent_games, stat)
        l5 = decayed if decayed is not None else season_avg

        # 32-team league midpoint (~16.5), mirrors NBA's 30-team (16) calibration.
        opp_rank = int(opp_ranks.get(stat, 16))
        opp_factor = max(-0.08, min(0.08, (16.5 - opp_rank) / 100))

        base = 0.5 * season_avg + 0.5 * l5
        projection = round(base * (1 + opp_factor), 1)

        results.append({
            "player_id": player_id,
            "player_name": player.get("PLAYER_NAME", ""),
            "team_abbreviation": player.get("TEAM_ABBREVIATION", ""),
            "stat": stat,
            "season_avg": round(season_avg, 1),
            "reg_season_avg": round(season_avg, 1),
            "playoff_avg": None,
            "last5_avg": round(l5, 1) if l5 is not None else round(season_avg, 1),
            "last10_avg": round(l5, 1) if l5 is not None else round(season_avg, 1),
            "opponent_rank": opp_rank,
            "projection": projection,
        })
    return results
