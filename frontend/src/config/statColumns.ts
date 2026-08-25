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
  // Populated in Phase 4 (NFL backend/frontend).
  nfl: [],
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
  nfl: [],
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
  nfl: [],
  soccer: [],
}

export const YESTERDAY_STAT_ORDER: Record<Sport, string[]> = {
  nba: ['PTS', 'REB', 'AST', 'FG3M', 'BLK', 'STL'],
  nfl: [],
  soccer: [],
}

export const YESTERDAY_STAT_LABEL: Record<Sport, Record<string, string>> = {
  nba: { PTS: 'Points', REB: 'Rebounds', AST: 'Assists', FG3M: '3-Pointers Made', BLK: 'Blocks', STL: 'Steals' },
  nfl: {},
  soccer: {},
}
