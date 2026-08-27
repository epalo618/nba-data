export type Sport = 'nba' | 'nfl'

export const SPORT_LABEL: Record<Sport, string> = {
  nba: 'NBA',
  nfl: 'NFL',
}

export interface Team {
  id: number
  full_name: string
  abbreviation: string
  city?: string
}

export interface Player {
  id: number
  full_name: string
  team_id?: number
}

export interface GameSummary {
  game_id?: string
  home_team_name: string
  away_team_name: string
  home_win_prob?: number
  away_win_prob?: number
  favored_team?: string | null
  projected_total?: number
}

export interface WinProbability {
  home_win_prob: number
  away_win_prob: number
  favored_team?: string | null
  reasons?: string[]
  factors?: Record<string, number>
}

export interface PlayerProjection {
  player_id: number
  player_name: string
  team_abbreviation: string
  stat: string
  season_avg: number
  projection: number
  last5_avg?: number
  last10_avg?: number
  reg_season_avg?: number
  playoff_avg?: number | null
  opponent_rank?: number
}
