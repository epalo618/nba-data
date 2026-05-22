import { useApi } from '../hooks/useApi'
import { gamesApi } from '../services/api'
import WinProbBar from '../components/WinProbBar'
import LoadingSpinner from '../components/LoadingSpinner'
import { Link } from 'react-router-dom'
import clsx from 'clsx'

export default function Games() {
  const { data, loading } = useApi(() => gamesApi.getToday())
  const games = (data as any)?.games ?? []

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Today's NBA Games</h1>

      {loading ? (
        <LoadingSpinner label="Fetching games..." />
      ) : games.length === 0 ? (
        <div className="bg-surface-card border border-surface-border rounded-xl p-8 text-center text-gray-500">
          No games scheduled today.
        </div>
      ) : (
        <div className="space-y-4">
          {games.map((game: any, i: number) => (
            <div key={i} className="bg-surface-card border border-surface-border rounded-xl p-6">
              <div className="flex justify-between items-start mb-5">
                <div>
                  <div className="text-white font-bold text-lg">{game.home_team_name}</div>
                  <div className="text-gray-500 text-xs mt-0.5">HOME</div>
                </div>
                <div className="text-center">
                  <div className="text-brand font-bold text-xl">VS</div>
                  {game.GAME_STATUS_TEXT && (
                    <div className="text-xs text-gray-500 mt-1">{game.GAME_STATUS_TEXT}</div>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-white font-bold text-lg">{game.away_team_name}</div>
                  <div className="text-gray-500 text-xs mt-0.5">AWAY</div>
                </div>
              </div>

              <WinProbBar
                homeTeam={game.home_team_name?.split(' ').pop() ?? ''}
                awayTeam={game.away_team_name?.split(' ').pop() ?? ''}
                homeProb={game.home_win_prob ?? 0.5}
                awayProb={game.away_win_prob ?? 0.5}
              />

              {game.favored_team && (
                <div className="mt-4 mb-2">
                  <div className="text-xs text-brand font-semibold uppercase tracking-wide mb-1.5">
                    Projected Winner: {game.favored_team}
                  </div>
                  <ul className="space-y-1">
                    {(game.win_reasons ?? []).map((r: string, ri: number) => (
                      <li key={ri} className="text-xs text-gray-400 flex gap-1.5">
                        <span className="text-brand mt-0.5">›</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="grid grid-cols-3 gap-4 mt-4 border-t border-surface-border pt-4 text-sm">
                <div className="text-center">
                  <div className="text-gray-500 text-xs">Proj Total</div>
                  <div className="text-white font-bold">{game.projected_total ?? '—'}</div>
                </div>
                <div className="text-center">
                  <div className="text-gray-500 text-xs">O/U Line</div>
                  <div className="text-white font-bold">{game.over_under_line ?? '—'}</div>
                </div>
                <div className="text-center">
                  <div className="text-gray-500 text-xs">Recommendation</div>
                  <div className={clsx('font-bold', game.over_under_rec === 'OVER' ? 'text-green-400' : game.over_under_rec === 'UNDER' ? 'text-red-400' : 'text-gray-400')}>
                    {game.over_under_rec ?? '—'}
                  </div>
                </div>
              </div>

              <div className="mt-4 text-right">
                <Link
                  to={`/games/${game.HOME_TEAM_ID}/vs/${game.VISITOR_TEAM_ID}`}
                  className="text-brand text-sm hover:underline font-medium"
                >
                  Full Matchup Analysis →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
