import axios from 'axios'
import type { Sport } from '../types/domain'

export type { Sport }

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? '/api' })

export const teamsApi = {
  getAll: (sport: Sport) => api.get(`/${sport}/teams/`),
  getStats: (sport: Sport) => api.get(`/${sport}/teams/stats`),
  getGamelog: (sport: Sport, teamId: number, n = 10) =>
    api.get(`/${sport}/teams/${teamId}/gamelog?n=${n}`),
}

export const playersApi = {
  getAll: (sport: Sport) => api.get(`/${sport}/players/`),
  getStats: (sport: Sport, teamId?: number) =>
    api.get(`/${sport}/players/stats` + (teamId ? `?team_id=${teamId}` : '')),
  getGamelog: (sport: Sport, playerId: string | number, n = 10) =>
    api.get(`/${sport}/players/${playerId}/gamelog?n=${n}`),
}

export const gamesApi = {
  getToday: (sport: Sport) => api.get(`/${sport}/games/today`),
  getMatchup: (sport: Sport, homeId: number, awayId: number) =>
    api.get(`/${sport}/games/${homeId}/vs/${awayId}`),
}

export const predictionsApi = {
  getPlayerProjections: (sport: Sport, playerId: string | number, opponentTeamId: number) =>
    api.get(`/${sport}/predictions/player/${playerId}/vs/${opponentTeamId}`),
  getGamePlayerProjections: (sport: Sport, homeId: number, awayId: number, topN = 8) =>
    api.get(`/${sport}/predictions/game/${homeId}/vs/${awayId}/players?top_n=${topN}`),
  getBestBets: (sport: Sport) => api.get(`/${sport}/predictions/best-bets`),
  getYesterday: (sport: Sport) => api.get(`/${sport}/predictions/yesterday`),
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
