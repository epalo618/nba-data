from datetime import datetime
from zoneinfo import ZoneInfo
import nflreadpy as nfl
from app.services.cache_utils import make_cache

# NFL uses a single-year season string, unlike NBA's "2025-26". Needs a manual
# bump each September once nflverse has that season's data flowing.
CURRENT_SEASON = 2025

CACHE_TTL = 3600  # 1 hour
_cached = make_cache(CACHE_TTL)


# nflreadpy's load_teams() includes relocated/retired franchise rows (e.g. STL/LA
# Rams, SD/LAC Chargers, OAK/LV Raiders) that share a team_id with their current
# incarnation. Exclude the retired abbreviations so ids stay 1:1 with 32 teams.
# Note: the Rams' *current* abbreviation in schedules/team_stats/player_stats is
# "LA", not "LAR" — load_teams() lists both as non-retired, so "LAR" (unused in
# any game-level data) is the one to drop here, not "LA".
_RETIRED_ABBRS = {"LAR", "STL", "SD", "OAK"}

# Position-specific prop categories (nflreadpy's player-stats column names, upper-cased).
POSITION_STAT_COLS = {
    "QB": ["PASSING_YARDS", "PASSING_TDS", "PASSING_INTERCEPTIONS"],
    "RB": ["RUSHING_YARDS", "RUSHING_TDS", "RECEPTIONS"],
    "WR": ["RECEIVING_YARDS", "RECEPTIONS", "RECEIVING_TDS"],
    "TE": ["RECEIVING_YARDS", "RECEPTIONS", "RECEIVING_TDS"],
}

_PLAYER_STAT_COLS = [
    "passing_yards", "passing_tds", "passing_interceptions",
    "carries", "rushing_yards", "rushing_tds",
    "receptions", "targets", "receiving_yards", "receiving_tds",
    "fantasy_points",
]


def _team_id_map() -> dict:
    """Builds abbr<->int-id<->full-name lookups once from load_teams()."""
    def fetch():
        teams = nfl.load_teams().to_dicts()
        current = [t for t in teams if t["team_abbr"] not in _RETIRED_ABBRS]
        abbr_to_id = {t["team_abbr"]: int(t["team_id"]) for t in current}
        id_to_abbr = {v: k for k, v in abbr_to_id.items()}
        id_to_name = {int(t["team_id"]): t["team_name"] for t in current}
        return {"abbr_to_id": abbr_to_id, "id_to_abbr": id_to_abbr, "id_to_name": id_to_name}
    return _cached("team_id_map", fetch, ttl=86400)


def _team_game_results(season: int = CURRENT_SEASON) -> list[dict]:
    """One row per team per played game: points for/against, W/L, week."""
    def fetch():
        sched = nfl.load_schedules(seasons=[season]).to_dicts()
        rows = []
        for g in sched:
            if g.get("home_score") is None or g.get("away_score") is None:
                continue
            home, away = g["home_team"], g["away_team"]
            hs, aws = g["home_score"], g["away_score"]
            rows.append({"team": home, "opp": away, "pts_for": hs, "pts_against": aws,
                         "win": hs > aws, "tie": hs == aws, "game_id": g["game_id"], "week": g["week"]})
            rows.append({"team": away, "opp": home, "pts_for": aws, "pts_against": hs,
                         "win": aws > hs, "tie": hs == aws, "game_id": g["game_id"], "week": g["week"]})
        return rows
    return _cached(f"team_game_results_{season}", fetch)


def get_all_teams(league: str | None = None):
    m = _team_id_map()
    return [
        {"id": tid, "full_name": m["id_to_name"][tid], "abbreviation": abbr, "nickname": "", "city": "", "state": "", "year_founded": None}
        for abbr, tid in m["abbr_to_id"].items()
    ]


def get_all_active_players(league: str | None = None):
    def fetch():
        players = nfl.load_players().to_dicts()
        m = _team_id_map()
        return [
            {"id": p["gsis_id"], "full_name": p.get("display_name"), "team_id": m["abbr_to_id"].get(p.get("latest_team")), "position": p.get("position")}
            for p in players if p.get("status") == "ACT"
        ]
    return _cached("all_active_players", fetch, ttl=86400)


def get_team_season_stats(league: str | None = None):
    def fetch():
        m = _team_id_map()
        by_team: dict = {}
        for r in _team_game_results():
            by_team.setdefault(r["team"], []).append(r)
        out = []
        for abbr, games in by_team.items():
            tid = m["abbr_to_id"].get(abbr)
            if tid is None or not games:
                continue
            gp = len(games)
            wins = sum(1 for g in games if g["win"])
            ties = sum(1 for g in games if g["tie"])
            losses = gp - wins - ties
            out.append({
                "TEAM_ID": tid,
                "TEAM_NAME": m["id_to_name"].get(tid, abbr),
                "GP": gp, "W": wins, "L": losses, "T": ties,
                "W_PCT": round(wins / gp, 3),
                "PTS": round(sum(g["pts_for"] for g in games) / gp, 1),
                "PTS_ALLOWED": round(sum(g["pts_against"] for g in games) / gp, 1),
            })
        return out
    return _cached(f"team_season_stats_{CURRENT_SEASON}", fetch)


def _team_stats_rows(season: int = CURRENT_SEASON) -> list[dict]:
    """Raw per-team-per-game stat rows from nflreadpy, cached once and shared by
    every caller that needs them (get_team_advanced_stats, get_opponent_stat_ranks)
    instead of each re-fetching/re-parsing the whole season table independently."""
    return _cached(f"raw_team_stats_{season}", lambda: nfl.load_team_stats(seasons=[season]).to_dicts())


def get_team_advanced_stats(league: str | None = None):
    """NFL-appropriate 'advanced' stats: yards/game, turnovers/game, point differential.
    Deliberately uses different keys than NBA's OFF_RATING/DEF_RATING/NET_RATING/PACE —
    the frontend's NFL column config (Phase 5) reads these key names directly."""
    def fetch():
        m = _team_id_map()
        ts_by_team: dict = {}
        for row in _team_stats_rows():
            ts_by_team.setdefault(row["team"], []).append(row)
        results_by_team: dict = {}
        for r in _team_game_results():
            results_by_team.setdefault(r["team"], []).append(r)

        out = []
        for abbr, rows in ts_by_team.items():
            tid = m["abbr_to_id"].get(abbr)
            gp = len(rows)
            if tid is None or gp == 0:
                continue
            yds = sum((row.get("passing_yards") or 0) + (row.get("rushing_yards") or 0) for row in rows) / gp
            turnovers = sum(
                (row.get("passing_interceptions") or 0)
                + (row.get("rushing_fumbles_lost") or 0)
                + (row.get("receiving_fumbles_lost") or 0)
                + (row.get("sack_fumbles_lost") or 0)
                for row in rows
            ) / gp
            game_results = results_by_team.get(abbr, [])
            pt_diff = sum(g["pts_for"] - g["pts_against"] for g in game_results) / len(game_results) if game_results else 0
            out.append({
                "TEAM_ID": tid,
                "YDS_PER_GAME": round(yds, 1),
                "TO_PER_GAME": round(turnovers, 1),
                "PT_DIFF": round(pt_diff, 1),
            })
        return out
    return _cached(f"team_advanced_stats_{CURRENT_SEASON}", fetch)


def get_player_season_stats(league: str | None = None):
    def fetch():
        m = _team_id_map()
        ps = nfl.load_player_stats(seasons=[CURRENT_SEASON]).to_dicts()
        reg = [r for r in ps if r.get("season_type") == "REG"]
        by_player: dict = {}
        for r in reg:
            by_player.setdefault(r["player_id"], []).append(r)

        out = []
        for pid, rows in by_player.items():
            gp = len(rows)
            if gp == 0:
                continue
            last = rows[-1]
            row = {
                "PLAYER_ID": pid,
                "PLAYER_NAME": last.get("player_display_name"),
                "TEAM_ABBREVIATION": last.get("team"),
                "TEAM_ID": m["abbr_to_id"].get(last.get("team")),
                "POSITION": last.get("position"),
                "GP": gp,
            }
            for col in _PLAYER_STAT_COLS:
                vals = [r.get(col) or 0 for r in rows]
                row[col.upper()] = round(sum(vals) / gp, 1)
            # No "minutes played" concept in NFL box scores, but callers that pick
            # "top players" (e.g. the game-matchup endpoint) sort by a MIN field
            # generically — reuse that key with total fantasy points as a stand-in
            # for on-field relevance, so QB/RB/WR/TE surface ahead of kickers etc.
            row["MIN"] = round(row["FANTASY_POINTS"] * gp, 1)
            out.append(row)
        return out
    return _cached(f"player_season_stats_{CURRENT_SEASON}", fetch)


def get_opponent_stat_ranks(league: str | None = None) -> dict:
    """Single overall defensive rank (by total yards allowed/game) applied to every
    stat category — a v1 simplification vs. NBA's true per-stat opponent ranking."""
    def fetch():
        m = _team_id_map()
        by_opp: dict = {}
        for row in _team_stats_rows():
            opp = row.get("opponent_team")
            yds = (row.get("passing_yards") or 0) + (row.get("rushing_yards") or 0)
            by_opp.setdefault(opp, []).append(yds)
        avg_allowed = {opp: sum(v) / len(v) for opp, v in by_opp.items() if v}
        # rank 1 = allows the most yards = worst defense = easiest matchup (mirrors NBA's convention)
        sorted_teams = sorted(avg_allowed.items(), key=lambda x: -x[1])

        stat_keys = [f"{c.upper()}" for cols in POSITION_STAT_COLS.values() for c in cols]
        ranks: dict = {}
        for i, (abbr, _) in enumerate(sorted_teams):
            tid = m["abbr_to_id"].get(abbr)
            if tid is None:
                continue
            ranks[tid] = {stat: i + 1 for stat in set(stat_keys)}
        return ranks
    return _cached(f"opponent_stat_ranks_{CURRENT_SEASON}", fetch)


def get_games_for_date(date_str: str, league: str | None = None) -> dict:
    def fetch():
        m = _team_id_map()
        games = []
        for g in nfl.load_schedules(seasons=[CURRENT_SEASON]).to_dicts():
            if g.get("gameday") != date_str:
                continue
            home_abbr, away_abbr = g["home_team"], g["away_team"]
            home_id, away_id = m["abbr_to_id"].get(home_abbr), m["abbr_to_id"].get(away_abbr)
            played = g.get("home_score") is not None
            games.append({
                "GAME_ID": g["game_id"],
                "GAME_STATUS_TEXT": "Final" if played else str(g.get("gametime") or "Scheduled"),
                "GAME_STATUS_ID": 3 if played else 1,
                "HOME_TEAM_ID": home_id,
                "HOME_TEAM_CITY": "", "HOME_TEAM_NAME": m["id_to_name"].get(home_id, home_abbr),
                "HOME_SCORE": g.get("home_score") or 0,
                "VISITOR_TEAM_ID": away_id,
                "VISITOR_TEAM_CITY": "", "VISITOR_TEAM_NAME": m["id_to_name"].get(away_id, away_abbr),
                "VISITOR_SCORE": g.get("away_score") or 0,
            })
        return {"games": games, "line_score": []}
    return _cached(f"games_{date_str}_{CURRENT_SEASON}", fetch)


def get_todays_games(league: str | None = None):
    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    return get_games_for_date(today)


def get_team_last_n_games(team_id: int, n: int = 10, league: str | None = None):
    def fetch():
        m = _team_id_map()
        abbr = m["id_to_abbr"].get(team_id)
        if not abbr:
            return []
        results = [r for r in _team_game_results() if r["team"] == abbr]
        results.sort(key=lambda r: r["week"], reverse=True)
        return [{"PTS": g["pts_for"], "PTS_ALLOWED": g["pts_against"], "GAME_ID": g["game_id"], "WEEK": g["week"]} for g in results[:n]]
    return _cached(f"team_gamelog_{team_id}_{CURRENT_SEASON}", fetch)


def get_head_to_head(team_id: int, opp_team_id: int, league: str | None = None) -> dict:
    def fetch():
        m = _team_id_map()
        abbr, opp_abbr = m["id_to_abbr"].get(team_id), m["id_to_abbr"].get(opp_team_id)
        if not abbr or not opp_abbr:
            return {"team_wins": 0, "opp_wins": 0, "games_played": 0}
        results = [r for r in _team_game_results() if r["team"] == abbr and r["opp"] == opp_abbr]
        wins = sum(1 for r in results if r["win"])
        losses = sum(1 for r in results if not r["win"] and not r["tie"])
        return {"team_wins": wins, "opp_wins": losses, "games_played": len(results)}
    return _cached(f"h2h_{team_id}_{opp_team_id}_{CURRENT_SEASON}", fetch)


def get_player_last_n_games(player_id: str, n: int = 10, league: str | None = None):
    def fetch():
        ps = nfl.load_player_stats(seasons=[CURRENT_SEASON]).to_dicts()
        rows = [r for r in ps if r.get("player_id") == player_id and r.get("season_type") == "REG"]
        rows.sort(key=lambda r: r["week"], reverse=True)
        out = []
        for r in rows[:n]:
            g = {"GAME_ID": r["game_id"], "WEEK": r["week"]}
            for col in _PLAYER_STAT_COLS:
                g[col.upper()] = r.get(col) or 0
            out.append(g)
        return out
    return _cached(f"player_gamelog_{player_id}_{CURRENT_SEASON}", fetch)


def get_game_boxscore(game_id: str, league: str | None = None) -> list[dict]:
    def fetch():
        ps = nfl.load_player_stats(seasons=[CURRENT_SEASON]).to_dicts()
        return [r for r in ps if r.get("game_id") == game_id]
    return _cached(f"boxscore_{game_id}", fetch)


def get_team_game_results_for_date(date_str: str, league: str | None = None) -> list[dict]:
    """Row shape mirrors nba_api's LeagueGameLog (GAME_ID/TEAM_ID/MATCHUP/WL/PTS)
    so record.py's existing MATCHUP-string parsing works unchanged once Phase 3
    wires the tracker up for non-NBA sports."""
    def fetch():
        m = _team_id_map()
        rows = []
        for g in nfl.load_schedules(seasons=[CURRENT_SEASON]).to_dicts():
            if g.get("gameday") != date_str or g.get("home_score") is None:
                continue
            home, away = g["home_team"], g["away_team"]
            hs, aws = g["home_score"], g["away_score"]
            home_id, away_id = m["abbr_to_id"].get(home), m["abbr_to_id"].get(away)
            rows.append({"GAME_ID": g["game_id"], "TEAM_ID": home_id, "TEAM_NAME": m["id_to_name"].get(home_id, home),
                        "MATCHUP": f"{home} vs. {away}", "WL": "W" if hs > aws else "L", "PTS": hs})
            rows.append({"GAME_ID": g["game_id"], "TEAM_ID": away_id, "TEAM_NAME": m["id_to_name"].get(away_id, away),
                        "MATCHUP": f"{away} @ {home}", "WL": "W" if aws > hs else "L", "PTS": aws})
        return rows
    return _cached(f"team_game_results_{date_str}", fetch)


def get_player_stats_for_date(date_str: str, league: str | None = None) -> list[dict]:
    def fetch():
        game_ids = {g["game_id"] for g in nfl.load_schedules(seasons=[CURRENT_SEASON]).to_dicts() if g.get("gameday") == date_str}
        if not game_ids:
            return []
        ps = nfl.load_player_stats(seasons=[CURRENT_SEASON]).to_dicts()
        out = []
        for r in ps:
            if r.get("game_id") not in game_ids:
                continue
            participated = any(r.get(k) for k in ("attempts", "carries", "targets", "def_tackles_solo"))
            row = {"GAME_ID": r["game_id"], "PLAYER_ID": r["player_id"], "MIN": "60" if participated else "0"}
            for col in _PLAYER_STAT_COLS:
                row[col.upper()] = r.get(col) or 0
            out.append(row)
        return out
    return _cached(f"player_stats_date_{date_str}", fetch, ttl=300)
