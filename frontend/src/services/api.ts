import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? '/api' })

export const teamsApi = {
  getAll: () => api.get('/teams/'),
  getStats: () => api.get('/teams/stats'),
  getGamelog: (teamId: number, n = 10) => api.get(`/teams/${teamId}/gamelog?n=${n}`),
}

export const playersApi = {
  getAll: () => api.get('/players/'),
  getStats: (teamId?: number) =>
    api.get('/players/stats' + (teamId ? `?team_id=${teamId}` : '')),
  getGamelog: (playerId: number, n = 10) => api.get(`/players/${playerId}/gamelog?n=${n}`),
}

export const gamesApi = {
  getToday: () => api.get('/games/today'),
  getMatchup: (homeId: number, awayId: number) => api.get(`/games/${homeId}/vs/${awayId}`),
}

export const predictionsApi = {
  getPlayerProjections: (playerId: number, opponentTeamId: number) =>
    api.get(`/predictions/player/${playerId}/vs/${opponentTeamId}`),
  getGamePlayerProjections: (homeId: number, awayId: number, topN = 8) =>
    api.get(`/predictions/game/${homeId}/vs/${awayId}/players?top_n=${topN}`),
  getBestBets: () => api.get('/predictions/best-bets'),
  getYesterday: () => api.get('/predictions/yesterday'),
}

export const recordApi = {
  get: () => api.get('/record'),
  getPoints: () => api.get('/record/points'),
  submit: (game_id: string, predicted_winner: string, actual_winner: string) =>
    api.post('/record/submit', { game_id, predicted_winner, actual_winner }),
  sync: () => api.post('/record/sync', {}),
  syncPoints: () => api.post('/record/points/sync', {}),
}
