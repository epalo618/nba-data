from app.services import nfl_service
from app.services.nfl_service import POSITION_STAT_COLS
from app.services.predictions_common import _norm_cdf, _decay_avg

# Starting estimates only — NFL public-analytics figures commonly cited in this
# range. Backtest against real tracker results (Phase 8) and adjust.
HOME_FIELD_NFL = 2.0
NFL_STD = 13.5


def calculate_win_probability(
    home_team_id: int,
    away_team_id: int,
    home_name: str = "Home",
    away_name: str = "Away",
    league: str | None = None,
) -> dict:
    season = {r["TEAM_ID"]: r for r in nfl_service.get_team_season_stats()}
    home_season = season.get(home_team_id, {})
    away_season = season.get(away_team_id, {})
    home_net = home_season.get("PTS", 21) - home_season.get("PTS_ALLOWED", 21)
    away_net = away_season.get("PTS", 21) - away_season.get("PTS_ALLOWED", 21)

    home_games = nfl_service.get_team_last_n_games(home_team_id, 5)
    away_games = nfl_service.get_team_last_n_games(away_team_id, 5)

    def recent_diff(games: list) -> float:
        diffs = [g.get("PTS", 0) - g.get("PTS_ALLOWED", 0) for g in games]
        return sum(diffs) / len(diffs) if diffs else 0.0

    home_recent = recent_diff(home_games)
    away_recent = recent_diff(away_games)

    home_adj = 0.65 * home_net + 0.35 * home_recent
    away_adj = 0.65 * away_net + 0.35 * away_recent
    spread = (home_adj - away_adj) + HOME_FIELD_NFL
    home_prob = _norm_cdf(spread / NFL_STD)
    away_prob = 1 - home_prob

    favored = home_name if home_prob >= 0.5 else away_name
    underdog = away_name if home_prob >= 0.5 else home_name
    fav_net = home_net if home_prob >= 0.5 else away_net
    dog_net = away_net if home_prob >= 0.5 else home_net

    reasons = []
    gap = abs(fav_net - dog_net)
    if gap >= 5:
        reasons.append(f"{favored} has a {gap:.1f} pt/game scoring-margin edge over {underdog} this season ({fav_net:+.1f} vs {dog_net:+.1f}).")
    if home_prob >= 0.5:
        reasons.append(f"{favored} has home field advantage (~{HOME_FIELD_NFL:.1f} pts on average).")
    else:
        reasons.append(f"{favored}'s scoring-margin edge overcomes {home_name}'s home field advantage.")
    if not reasons:
        reasons.append(f"Close matchup — {favored} holds a slight edge based on scoring margin.")

    return {
        "home_win_prob": round(home_prob, 3),
        "away_win_prob": round(away_prob, 3),
        "favored_team": favored,
        "reasons": reasons,
        "factors": {
            "home_net": round(home_net, 2),
            "away_net": round(away_net, 2),
            "projected_spread": round(spread, 1),
        },
    }


def calculate_projected_total(home_team_id: int, away_team_id: int, league: str | None = None) -> float:
    season = {r["TEAM_ID"]: r for r in nfl_service.get_team_season_stats()}
    home = season.get(home_team_id, {})
    away = season.get(away_team_id, {})
    home_ppg = home.get("PTS", 21)
    home_papg = home.get("PTS_ALLOWED", 21)
    away_ppg = away.get("PTS", 21)
    away_papg = away.get("PTS_ALLOWED", 21)
    season_proj = (home_ppg + away_papg) / 2 + (away_ppg + home_papg) / 2

    try:
        home_games = nfl_service.get_team_last_n_games(home_team_id, 5)
        away_games = nfl_service.get_team_last_n_games(away_team_id, 5)

        def _avg(games, field):
            vals = [g[field] for g in games if g.get(field) is not None]
            return sum(vals) / len(vals) if vals else None

        h_scored, h_allowed = _avg(home_games, "PTS"), _avg(home_games, "PTS_ALLOWED")
        a_scored, a_allowed = _avg(away_games, "PTS"), _avg(away_games, "PTS_ALLOWED")
        if all(v is not None for v in [h_scored, h_allowed, a_scored, a_allowed]):
            recent_proj = (h_scored + a_allowed) / 2 + (a_scored + h_allowed) / 2
            return round(0.6 * recent_proj + 0.4 * season_proj, 1)
    except Exception:
        pass
    return round(season_proj, 1)


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
