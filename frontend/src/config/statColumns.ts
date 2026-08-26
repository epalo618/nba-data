import type { Sport } from '../types/domain'

export interface ColumnConfig {
  key: string
  label: string
  percent?: boolean
  signColor?: boolean
  decimals?: number
}

export const TEAM_COLUMNS: Record<Sport, ColumnConfig[]> = {
  nba: [
    { key: 'W', label: 'W' },
    { key: 'L', label: 'L' },
    { key: 'W_PCT', label: 'WIN%', percent: true },
    { key: 'PTS', label: 'PTS' },
    { key: 'REB', label: 'REB' },
    { key: 'AST', label: 'AST' },
    { key: 'STL', label: 'STL' },
    { key: 'BLK', label: 'BLK' },
    { key: 'TOV', label: 'TOV' },
    { key: 'OFF_RATING', label: 'ORTG' },
    { key: 'DEF_RATING', label: 'DRTG' },
    { key: 'NET_RATING', label: 'NET', signColor: true },
    { key: 'PACE', label: 'PACE' },
  ],
  nfl: [
    { key: 'W', label: 'W' },
    { key: 'L', label: 'L' },
    { key: 'T', label: 'T' },
    { key: 'W_PCT', label: 'WIN%', percent: true },
    { key: 'PTS', label: 'PPG' },
    { key: 'PTS_ALLOWED', label: 'PAPG' },
    { key: 'YDS_PER_GAME', label: 'YDS/G' },
    { key: 'TO_PER_GAME', label: 'TO/G' },
    { key: 'PT_DIFF', label: 'DIFF', signColor: true },
  ],
  // Populated in Phase 6/7 (soccer backend/frontend).
  soccer: [],
}

export const PLAYER_COLUMNS: Record<Sport, ColumnConfig[]> = {
  nba: [
    { key: 'GP', label: 'GP' },
    { key: 'MIN', label: 'MIN' },
    { key: 'PTS', label: 'PTS' },
    { key: 'REB', label: 'REB' },
    { key: 'AST', label: 'AST' },
    { key: 'STL', label: 'STL' },
    { key: 'BLK', label: 'BLK' },
    { key: 'TOV', label: 'TOV' },
    { key: 'FG_PCT', label: 'FG%', percent: true },
    { key: 'FG3_PCT', label: '3P%', percent: true },
    { key: 'FT_PCT', label: 'FT%', percent: true },
    { key: 'PLUS_MINUS', label: '+/-', signColor: true },
  ],
  nfl: [
    { key: 'GP', label: 'GP' },
    { key: 'PASSING_YARDS', label: 'PASS YDS' },
    { key: 'PASSING_TDS', label: 'PASS TD' },
    { key: 'RUSHING_YARDS', label: 'RUSH YDS' },
    { key: 'RUSHING_TDS', label: 'RUSH TD' },
    { key: 'RECEPTIONS', label: 'REC' },
    { key: 'RECEIVING_YARDS', label: 'REC YDS' },
    { key: 'RECEIVING_TDS', label: 'REC TD' },
    { key: 'FANTASY_POINTS', label: 'FPTS' },
  ],
  soccer: [],
}

export const DEFAULT_PLAYER_SORT: Record<Sport, string> = {
  nba: 'PTS',
  nfl: 'FANTASY_POINTS',
  soccer: '',
}

export interface SummaryCardConfig {
  key: string
  label: string
  decimals?: number
}

// Drives GameMatchup's per-team summary cards (MatchupStatCards) — three
// headline stats per sport, read straight off get_team_season_stats /
// get_team_advanced_stats' keys.
export const MATCHUP_SUMMARY_CARDS: Record<Sport, SummaryCardConfig[]> = {
  nba: [
    { key: 'PTS', label: 'PTS/G' },
    { key: 'OFF_RATING', label: 'OFF RTG' },
    { key: 'DEF_RATING', label: 'DEF RTG' },
  ],
  nfl: [
    { key: 'PTS', label: 'PPG' },
    { key: 'PTS_ALLOWED', label: 'PAPG' },
    { key: 'YDS_PER_GAME', label: 'YDS/G' },
  ],
  soccer: [],
}

export interface PredictionStatCategory {
  key: string
  label: string
}

export const PREDICTION_STAT_CATEGORIES: Record<Sport, PredictionStatCategory[]> = {
  nba: [
    { key: 'PTS', label: 'Points Props' },
    { key: 'REB', label: 'Rebound Props' },
    { key: 'AST', label: 'Assist Props' },
    { key: 'FG3M', label: '3-Pointers Made' },
  ],
  // NFL's stat categories are already position-exclusive by construction (see
  // nfl_service.POSITION_STAT_COLS) — a QB only ever generates PASSING_* props,
  // a WR/TE only RECEIVING_*/RECEPTIONS — so grouping by stat category here
  // naturally reads as position-grouped without needing a separate render path.
  nfl: [
    { key: 'PASSING_YARDS', label: 'Passing Yards' },
    { key: 'PASSING_TDS', label: 'Passing TDs' },
    { key: 'RUSHING_YARDS', label: 'Rushing Yards' },
    { key: 'RECEIVING_YARDS', label: 'Receiving Yards' },
    { key: 'RECEPTIONS', label: 'Receptions' },
  ],
  soccer: [],
}

export const YESTERDAY_STAT_ORDER: Record<Sport, string[]> = {
  nba: ['PTS', 'REB', 'AST', 'FG3M', 'BLK', 'STL'],
  nfl: ['PASSING_YARDS', 'PASSING_TDS', 'RUSHING_YARDS', 'RECEIVING_YARDS', 'RECEPTIONS'],
  soccer: [],
}

export const YESTERDAY_STAT_LABEL: Record<Sport, Record<string, string>> = {
  nba: { PTS: 'Points', REB: 'Rebounds', AST: 'Assists', FG3M: '3-Pointers Made', BLK: 'Blocks', STL: 'Steals' },
  nfl: {
    PASSING_YARDS: 'Passing Yards', PASSING_TDS: 'Passing TDs',
    RUSHING_YARDS: 'Rushing Yards', RECEIVING_YARDS: 'Receiving Yards', RECEPTIONS: 'Receptions',
  },
  soccer: {},
}
