import { useApi } from '../hooks/useApi'
import { gamesApi, predictionsApi } from '../services/api'
import { useCurrentSport } from '../hooks/useCurrentSport'
import { SPORT_LABEL } from '../types/domain'
import WinProbBar from '../components/WinProbBar'
import WinProbBar3Way from '../components/WinProbBar3Way'
import LoadingSpinner from '../components/LoadingSpinner'
import { Link } from 'react-router-dom'
import clsx from 'clsx'

export default function Dashboard() {
  const { sport: s, league } = useCurrentSport()
  const { data: gamesData, loading: gamesLoading } = useApi(() => gamesApi.getToday(s, league), [s, league])
  const { data: bestBets, loading: betsLoading } = useApi(() => predictionsApi.getBestBets(s, league), [s, league])

  const games = (gamesData as any)?.games ?? []

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Today's Games</h1>
        <p className="text-gray-500 text-sm">Win probabilities and projected totals for all {SPORT_LABEL[s]} games today.</p>
      </div>

      {gamesLoading ? (
        <LoadingSpinner label="Fetching today's games..." />
      ) : games.length === 0 ? (
        <div className="bg-surface-card border border-surface-border rounded-xl p-8 text-center text-gray-500">
          No games scheduled today.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {games.map((game: any, i: number) => (
            <Link
              key={i}
              to={`/${s}/games/${game.HOME_TEAM_ID}/vs/${game.VISITOR_TEAM_ID}`}
              className="bg-surface-card border border-surface-border rounded-xl p-5 hover:border-brand transition-colors block"
            >
              <div className="flex justify-between items-center mb-4">
                <div>
                  <div className="text-white font-semibold">{game.away_team_name}</div>
                  <div className="text-gray-500 text-xs">AWAY</div>
                </div>
                <div className="text-center">
                  <div className="text-brand font-bold text-lg">vs</div>
                  {game.LEAGUE && (
                    <div className="text-xs text-gray-500 mt-0.5">{game.LEAGUE}</div>
                  )}
                  {game.h2h_games_played > 0 && (
                    <div className="text-xs text-gray-500 mt-0.5">
                      H2H {game.h2h_away_wins}-{game.h2h_home_wins}
                    </div>
                  )}
                  <div className="text-xs text-gray-500 mt-0.5">{game.GAME_STATUS_TEXT}</div>
                </div>
                <div className="text-right">
                  <div className="text-white font-semibold">{game.home_team_name}</div>
                  <div className="text-gray-500 text-xs">HOME</div>
                </div>
              </div>

              {s === 'soccer' ? (
                <WinProbBar3Way
                  homeTeam={game.home_team_name?.split(' ').pop() ?? ''}
                  awayTeam={game.away_team_name?.split(' ').pop() ?? ''}
                  homeProb={game.home_win_prob ?? 0.33}
                  drawProb={game.draw_prob ?? 0.34}
                  awayProb={game.away_win_prob ?? 0.33}
                />
              ) : (
                <WinProbBar
                  homeTeam={game.home_team_name?.split(' ').pop() ?? ''}
                  awayTeam={game.away_team_name?.split(' ').pop() ?? ''}
                  homeProb={game.home_win_prob ?? 0.5}
                  awayProb={game.away_win_prob ?? 0.5}
                />
              )}

              {game.favored_team && (
                <div className="mt-3 mb-1">
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

              <div className="flex justify-between mt-3 text-sm border-t border-surface-border pt-3">
                <div>
                  <span className="text-gray-500">{s === 'soccer' ? 'Proj Goals: ' : 'Proj Pts: '}</span>
                  <span className="text-white font-semibold">{Math.round(game.projected_total)}</span>
                </div>
                {game.over_under_line && (
                  <div>
                    <span className="text-gray-500">Line </span>
                    <span className="text-white font-semibold">{game.over_under_line}</span>
                    {game.over_under_rec && (
                      <span className={clsx('ml-2 text-xs font-bold',
                        game.over_under_rec === 'OVER' ? 'text-green-400' :
                        game.over_under_rec === 'UNDER' ? 'text-red-400' : 'text-gray-400'
                      )}>
                        {game.over_under_rec}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      <div>
        <h2 className="text-xl font-bold text-white mb-1">Top Prop Signals</h2>
        <p className="text-gray-500 text-sm mb-4">Projections where the model diverges most from season averages.</p>

        {s === 'soccer' ? (
          <div className="bg-surface-card border border-surface-border rounded-xl p-8 text-center text-gray-500">
            Player prop projections aren't available for soccer yet.
          </div>
        ) : betsLoading ? (
          <LoadingSpinner label="Calculating projections..." />
        ) : (
          <div className="bg-surface-card border border-surface-border rounded-xl overflow-hidden">
            <div className="grid grid-cols-8 gap-2 px-4 py-2 text-xs text-gray-500 uppercase border-b border-surface-border">
              <span>Player</span>
              <span>Stat</span>
              <span>Reg Avg</span>
              <span className="text-yellow-600">Post Avg</span>
              <span>Projection</span>
              <span className="col-span-2">Tot Avg</span>
              <span>Signal</span>
            </div>
            {((bestBets as any[]) ?? []).slice(0, 15).map((bet: any, i: number) => (
              <div key={i} className="grid grid-cols-8 gap-2 px-4 py-3 border-b border-surface-border hover:bg-surface-hover text-sm">
                <span className="text-white font-medium">{bet.player_name}</span>
                <span className="text-gray-400 font-semibold">{bet.stat}</span>
                <span className="text-gray-400">{bet.reg_season_avg ?? bet.season_avg}</span>
                <span className="text-yellow-400">{bet.playoff_avg ?? '—'}</span>
                <span className="text-white font-bold">{bet.projection}</span>
                <span className="text-gray-400 col-span-2">
                  {bet.season_avg ?? '—'}
                </span>
                <span className={clsx('font-bold text-xs',
                  bet.projection > bet.season_avg ? 'text-green-400' : 'text-red-400'
                )}>
                  {bet.projection > bet.season_avg ? '↑ OVER' : '↓ UNDER'}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="text-xs text-gray-600 text-center">
        Projections are statistical estimates only. Sports betting involves risk. Never bet more than you can afford to lose.
      </div>
    </div>
  )
}
