import time
from nba_api.stats.static import teams as nba_teams_static, players as nba_players_static
from datetime import date, datetime
from zoneinfo import ZoneInfo
from nba_api.stats.endpoints import (
    leaguedashteamstats,
    leaguedashplayerstats,
    leaguegamelog,
    scoreboardv3,
    teamgamelog,
    playergamelog,
    boxscoretraditionalv2,
)

CURRENT_SEASON = "2025-26"
_cache: dict = {}
CACHE_TTL = 3600  # 1 hour


def _cached(key: str, fn):
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < CACHE_TTL:
        return _cache[key]["data"]
    data = fn()
    _cache[key] = {"data": data, "ts": now}
    return data


def _get_all_game_scores() -> dict:
    """Returns {game_id: {team_id: pts}} for reg season + playoffs."""
    def fetch():
        reg_df = leaguegamelog.LeagueGameLog(
            season=CURRENT_SEASON,
            player_or_team_abbreviation="T",
            timeout=60,
        ).get_data_frames()[0]

        time.sleep(0.5)
        playoff_df = leaguegamelog.LeagueGameLog(
            season=CURRENT_SEASON,
            season_type_all_star="Playoffs",
            player_or_team_abbreviation="T",
            timeout=60,
        ).get_data_frames()[0]

        pts_map: dict = {}
        for df in [reg_df, playoff_df]:
            for row in df.to_dict(orient="records"):
                gid = row.get("GAME_ID")
                tid = row.get("TEAM_ID")
                pts = row.get("PTS")
                if gid and tid and pts is not None:
                    pts_map.setdefault(gid, {})[tid] = pts
        return pts_map
    return _cached("all_game_scores", fetch)


def get_all_teams():
    return nba_teams_static.get_teams()


def get_all_active_players():
    return nba_players_static.get_active_players()


def get_team_season_stats():
    def fetch():
        resp = leaguedashteamstats.LeagueDashTeamStats(
            season=CURRENT_SEASON,
            per_mode_detailed="PerGame",
            timeout=30,
        )
        df = resp.get_data_frames()[0]
        return df.to_dict(orient="records")
    return _cached("team_season_stats", fetch)


def get_team_advanced_stats():
    def fetch():
        resp = leaguedashteamstats.LeagueDashTeamStats(
            season=CURRENT_SEASON,
            measure_type_detailed_defense="Advanced",
            per_mode_detailed="PerGame",
            timeout=30,
        )
        df = resp.get_data_frames()[0]
        return df.to_dict(orient="records")
    return _cached("team_advanced_stats", fetch)


def get_player_season_stats():
    def fetch():
        reg_resp = leaguedashplayerstats.LeagueDashPlayerStats(
            season=CURRENT_SEASON,
            per_mode_detailed="PerGame",
            timeout=60,
        )
        reg_records = reg_resp.get_data_frames()[0].to_dict(orient="records")

        time.sleep(0.5)
        playoff_resp = leaguedashplayerstats.LeagueDashPlayerStats(
            season=CURRENT_SEASON,
            season_type_all_star="Playoffs",
            per_mode_detailed="PerGame",
            timeout=60,
        )
        playoff_records = playoff_resp.get_data_frames()[0].to_dict(orient="records")

        if not playoff_records:
            return reg_records

        blend_cols = ["PTS", "REB", "AST", "STL", "BLK", "MIN", "FG3M"]
        playoff_map = {r["PLAYER_ID"]: r for r in playoff_records}

        result = []
        for row in reg_records:
            pid = row["PLAYER_ID"]
            blended = dict(row)
            if pid in playoff_map:
                prow = playoff_map[pid]
                for col in blend_cols:
                    if col in row and col in prow:
                        blended[f"{col}_REG"] = round(row[col] or 0, 1)
                        blended[f"{col}_PLAYOFF"] = round(prow[col] or 0, 1)
                        blended[col] = round(0.5 * (row[col] or 0) + 0.5 * (prow[col] or 0), 1)
            else:
                for col in blend_cols:
                    if col in row:
                        blended[f"{col}_REG"] = round(row[col] or 0, 1)
                        blended[f"{col}_PLAYOFF"] = None
            result.append(blended)
        return result
    return _cached("player_season_stats", fetch)


def _parse_scoreboard(date_str: str) -> dict:
    """Fetch and parse scoreboard for a given YYYY-MM-DD date string."""
    resp = scoreboardv3.ScoreboardV3(game_date=date_str, timeout=30)
    dfs = resp.get_data_frames()
    games_df = dfs[1]
    teams_df = dfs[2]

    games = []
    for _, game_row in games_df.iterrows():
        game_id = game_row["gameId"]
        game_code = game_row.get("gameCode", "")
        code_part = game_code.split("/")[-1] if "/" in game_code else ""
        away_tricode = code_part[:3]
        home_tricode = code_part[3:]

        team_rows = teams_df[teams_df["gameId"] == game_id]
        home_row = team_rows[team_rows["teamTricode"] == home_tricode]
        away_row = team_rows[team_rows["teamTricode"] == away_tricode]

        if home_row.empty or away_row.empty:
            rows = team_rows.to_dict(orient="records")
            home_data = rows[0] if rows else {}
            away_data = rows[1] if len(rows) > 1 else {}
        else:
            home_data = home_row.iloc[0].to_dict()
            away_data = away_row.iloc[0].to_dict()

        games.append({
            "GAME_ID": game_id,
            "GAME_STATUS_TEXT": game_row.get("gameStatusText", ""),
            "GAME_STATUS_ID": game_row.get("gameStatus", 1),
            "GAME_TIME_UTC": game_row.get("gameTimeUTC", ""),
            "SERIES_GAME_NUMBER": game_row.get("seriesGameNumber", ""),
            "GAME_LABEL": game_row.get("gameLabel", ""),
            "SERIES_TEXT": game_row.get("seriesText", ""),
            "HOME_TEAM_ID": home_data.get("teamId"),
            "HOME_TEAM_CITY": home_data.get("teamCity", ""),
            "HOME_TEAM_NAME": home_data.get("teamName", ""),
            "HOME_TEAM_TRICODE": home_data.get("teamTricode", ""),
            "HOME_SCORE": home_data.get("score", 0),
            "VISITOR_TEAM_ID": away_data.get("teamId"),
            "VISITOR_TEAM_CITY": away_data.get("teamCity", ""),
            "VISITOR_TEAM_NAME": away_data.get("teamName", ""),
            "VISITOR_TEAM_TRICODE": away_data.get("teamTricode", ""),
            "VISITOR_SCORE": away_data.get("score", 0),
        })

    return {"games": games, "line_score": []}


def get_games_for_date(date_str: str) -> dict:
    def fetch():
        try:
            return _parse_scoreboard(date_str)
        except Exception:
            return {"games": [], "line_score": []}
    return _cached(f"games_{date_str}", fetch)


def get_todays_games():
    def fetch():
        # Use Eastern time so the date doesn't flip at 8 PM EST (midnight UTC)
        today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
        return _parse_scoreboard(today)

    # 60-second TTL so live scores refresh; all other caches stay at 1 hour
    key = "todays_games"
    now = time.time()
    if key in _cache and now - _cache[key]["ts"] < 60:
        return _cache[key]["data"]
    data = fetch()
    _cache[key] = {"data": data, "ts": now}
    return data


def get_team_last_n_games(team_id: int, n: int = 10):
    key = f"team_gamelog_{team_id}"
    def fetch():
        playoff_resp = teamgamelog.TeamGameLog(
            team_id=team_id,
            season=CURRENT_SEASON,
            season_type_all_star="Playoffs",
            timeout=30,
        )
        playoff_games = playoff_resp.get_data_frames()[0].to_dict(orient="records")

        if len(playoff_games) >= n:
            games = playoff_games[:n]
        else:
            time.sleep(0.3)
            reg_resp = teamgamelog.TeamGameLog(
                team_id=team_id,
                season=CURRENT_SEASON,
                timeout=30,
            )
            reg_games = reg_resp.get_data_frames()[0].to_dict(orient="records")
            games = (playoff_games + reg_games[:n - len(playoff_games)])[:n]

        # Enrich each game with PTS_ALLOWED using the league-wide scores map
        pts_map = _get_all_game_scores()
        for g in games:
            gid = g.get("Game_ID") or g.get("GAME_ID")
            game_scores = pts_map.get(gid, {})
            opp_pts = next((v for k, v in game_scores.items() if int(k) != team_id), None)
            g["PTS_ALLOWED"] = opp_pts if opp_pts is not None else g.get("PTS", 0)
        return games
    return _cached(key, fetch)


def get_head_to_head(team_id: int, opp_team_id: int) -> dict:
    """Returns this-season H2H record between two teams (playoffs + reg season)."""
    key = f"h2h_{min(team_id, opp_team_id)}_{max(team_id, opp_team_id)}"
    def fetch():
        all_static = nba_teams_static.get_teams()
        opp_info = next((t for t in all_static if t["id"] == opp_team_id), {})
        opp_abbr = opp_info.get("abbreviation", "")

        playoff_resp = teamgamelog.TeamGameLog(
            team_id=team_id,
            season=CURRENT_SEASON,
            season_type_all_star="Playoffs",
            timeout=60,
        )
        playoff_games = playoff_resp.get_data_frames()[0].to_dict(orient="records")

        time.sleep(0.3)
        reg_resp = teamgamelog.TeamGameLog(
            team_id=team_id,
            season=CURRENT_SEASON,
            timeout=60,
        )
        reg_games = reg_resp.get_data_frames()[0].to_dict(orient="records")

        all_games = playoff_games + reg_games
        h2h = [g for g in all_games if opp_abbr and opp_abbr in g.get("MATCHUP", "")]
        wins = sum(1 for g in h2h if g.get("WL") == "W")
        losses = sum(1 for g in h2h if g.get("WL") == "L")
        return {"team_wins": wins, "opp_wins": losses, "games_played": len(h2h)}
    return _cached(key, fetch)


def get_player_last_n_games(player_id: int, n: int = 10):
    key = f"player_gamelog_{player_id}"
    def fetch():
        playoff_resp = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=CURRENT_SEASON,
            season_type_all_star="Playoffs",
            timeout=60,
        )
        playoff_games = playoff_resp.get_data_frames()[0].to_dict(orient="records")

        if len(playoff_games) >= n:
            return playoff_games[:n]

        time.sleep(0.3)
        reg_resp = playergamelog.PlayerGameLog(
            player_id=player_id,
            season=CURRENT_SEASON,
            timeout=60,
        )
        reg_games = reg_resp.get_data_frames()[0].to_dict(orient="records")
        return (playoff_games + reg_games[:n - len(playoff_games)])[:n]
    return _cached(key, fetch)


def get_game_boxscore(game_id: str) -> list[dict]:
    def fetch():
        resp = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id, timeout=60)
        df = resp.get_data_frames()[0]  # player stats
        return df.to_dict(orient="records")
    return _cached(f"boxscore_{game_id}", fetch)


def get_player_stats_for_date(date_str: str) -> list[dict]:
    """All player game stats for a specific date (single API call, playoffs first)."""
    def fetch():
        for season_type in ["Playoffs", "Regular Season"]:
            try:
                resp = leaguegamelog.LeagueGameLog(
                    season=CURRENT_SEASON,
                    season_type_all_star=season_type,
                    player_or_team_abbreviation="P",
                    date_from_nullable=date_str,
                    date_to_nullable=date_str,
                    timeout=60,
                )
                records = resp.get_data_frames()[0].to_dict(orient="records")
                if records:
                    return records
            except Exception:
                pass
        return []
    return _cached(f"player_stats_date_{date_str}", fetch)
