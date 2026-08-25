import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? '/api' })

export type Sport = 'nba' | 'nfl' | 'soccer'

// Appends ?league=xxx when a league is given (soccer only) — kept as a tiny
// helper so every call site doesn't repeat the same ternary.
const lg = (league?: string) => (league ? `?league=${league}` : '')
const lgAmp = (league?: string) => (league ? `&league=${league}` : '')

export const teamsApi = {
  getAll: (sport: Sport, league?: string) => api.get(`/${sport}/teams/${lg(league)}`),
  getStats: (sport: Sport, league?: string) => api.get(`/${sport}/teams/stats${lg(league)}`),
  getGamelog: (sport: Sport, teamId: number, n = 10, league?: string) =>
    api.get(`/${sport}/teams/${teamId}/gamelog?n=${n}${lgAmp(league)}`),
}

export const playersApi = {
  getAll: (sport: Sport, league?: string) => api.get(`/${sport}/players/${lg(league)}`),
  getStats: (sport: Sport, teamId?: number, league?: string) =>
    api.get(`/${sport}/players/stats` + (teamId ? `?team_id=${teamId}${lgAmp(league)}` : lg(league))),
  getGamelog: (sport: Sport, playerId: number, n = 10, league?: string) =>
    api.get(`/${sport}/players/${playerId}/gamelog?n=${n}${lgAmp(league)}`),
}

export const gamesApi = {
  getToday: (sport: Sport, league?: string) => api.get(`/${sport}/games/today${lg(league)}`),
  getMatchup: (sport: Sport, homeId: number, awayId: number, league?: string) =>
    api.get(`/${sport}/games/${homeId}/vs/${awayId}${lg(league)}`),
}

export const predictionsApi = {
  getPlayerProjections: (sport: Sport, playerId: number, opponentTeamId: number, league?: string) =>
    api.get(`/${sport}/predictions/player/${playerId}/vs/${opponentTeamId}${lg(league)}`),
  getGamePlayerProjections: (sport: Sport, homeId: number, awayId: number, topN = 8, league?: string) =>
    api.get(`/${sport}/predictions/game/${homeId}/vs/${awayId}/players?top_n=${topN}${lgAmp(league)}`),
  getBestBets: (sport: Sport, league?: string) => api.get(`/${sport}/predictions/best-bets${lg(league)}`),
  getYesterday: (sport: Sport, league?: string) => api.get(`/${sport}/predictions/yesterday${lg(league)}`),
}

export const recordApi = {
  get: (sport: Sport) => api.get(`/${sport}/record`),
  getPoints: (sport: Sport) => api.get(`/${sport}/record/points`),
  getHistory: (sport: Sport) => api.get(`/${sport}/record/history`),
  getPointsHistory: (sport: Sport) => api.get(`/${sport}/record/points/history`),
  submit: (sport: Sport, game_id: string, predicted_winner: string, actual_winner: string) =>
    api.post(`/${sport}/record/submit`, { game_id, predicted_winner, actual_winner }),
  sync: (sport: Sport) => api.post(`/${sport}/record/sync`, {}),
  syncPoints: (sport: Sport) => api.post(`/${sport}/record/points/sync`, {}),
  debugPoints: (sport: Sport) => api.get(`/${sport}/record/points/debug`),
}
