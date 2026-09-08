import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { gamesApi, predictionsApi } from '../services/api'
import { useCurrentSport } from '../hooks/useCurrentSport'
import { SPORT_LABEL } from '../types/domain'
import WinProbBar from '../components/WinProbBar'
import LoadingSpinner from '../components/LoadingSpinner'
import { Link } from 'react-router-dom'
import clsx from 'clsx'

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function fmtMonthDay(iso: string): string {
  const [, m, d] = iso.split('-').map(Number)
  return `${m}/${d}`
}

function fmtDayHeading(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  const wd = WEEKDAYS[new Date(y, m - 1, d).getDay()]
  return `${wd} · ${m}/${d}`
}

interface WeekDay {
  date: string
  games: any[]
}

export default function Dashboard() {
  const { sport: s } = useCurrentSport()
  const [offset, setOffset] = useState(0)

  const { data: weekData, loading: gamesLoading } = useApi(
    () => gamesApi.getWeek(s, { offset }),
    [s, offset],
  )
  const { data: bestBets, loading: betsLoading } = useApi(() => predictionsApi.getBestBets(s), [s])

  const days: WeekDay[] = (weekData as any)?.days ?? []
  const daysWithGames = days.filter((d) => d.games.length > 0)
  const totalGames = (weekData as any)?.total_games ?? 0
  const bases = new Set(daysWithGames.flatMap((d) => d.games.map((g: any) => g.projection_basis)))
  const anyMarket = bases.has('market') || bases.has('blend')
  const anyNoData = bases.has('none')
  const rangeLabel =
    weekData && (weekData as any).start
      ? `${fmtMonthDay((weekData as any).start)}–${fmtMonthDay((weekData as any).end)}`
      : '…'

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">This Week's {SPORT_LABEL[s]} Games</h1>
        <p className="text-gray-500 text-sm">
          Win probabilities and projected totals for every {SPORT_LABEL[s]} game, Sunday through Saturday.
        </p>
      </div>

      {/* Week navigator */}
      <div className="sticky top-14 z-40 -mx-4 px-4 py-3 bg-surface/95 backdrop-blur border-b border-surface-border flex items-center justify-center gap-4">
        <button
          onClick={() => setOffset((o) => o - 1)}
          className="w-9 h-9 rounded-lg border border-surface-border text-gray-300 hover:border-brand hover:text-brand transition-colors flex items-center justify-center"
          aria-label="Previous week"
        >
          ‹
        </button>
        <div className="text-center min-w-[9rem]">
          <div className="text-white font-bold text-lg tabular-nums">{rangeLabel}</div>
          <button
            onClick={() => setOffset(0)}
            className={clsx(
              'text-xs transition-colors',
              offset === 0 ? 'text-gray-600' : 'text-brand hover:underline',
            )}
            disabled={offset === 0}
          >
            {offset === 0 ? 'This week' : 'Back to this week'}
          </button>
        </div>
        <button
          onClick={() => setOffset((o) => o + 1)}
          className="w-9 h-9 rounded-lg border border-surface-border text-gray-300 hover:border-brand hover:text-brand transition-colors flex items-center justify-center"
          aria-label="Next week"
        >
          ›
        </button>
      </div>

      {!gamesLoading && (anyMarket || anyNoData) && (
        <div className="-mt-4 text-xs text-gray-500 bg-surface-card border border-surface-border rounded-lg px-4 py-2.5">
          <span className="text-brand font-semibold">Early-season basis:</span>{' '}
          {anyMarket ? (
            <>
              with little data this season yet, win probability and projected points are anchored to the betting
              market, which already prices in offseason trades, the draft, and injury news. Each game shifts to
              the teams' own results as they're played.
            </>
          ) : (
            <>some games have no data this season and no betting line yet, so their projections are left blank.</>
          )}
        </div>
      )}

      {gamesLoading ? (
        <LoadingSpinner label="Fetching this week's games..." />
      ) : totalGames === 0 ? (
        <div className="bg-surface-card border border-surface-border rounded-xl p-8 text-center text-gray-500">
          No {SPORT_LABEL[s]} games scheduled this week. Use the arrows above to look ahead.
        </div>
      ) : (
        <div className="space-y-8">
          {daysWithGames.map((day) => (
            <div key={day.date}>
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
                {fmtDayHeading(day.date)}
                <span className="text-gray-600 font-normal ml-2 normal-case tracking-normal">
                  {day.games.length} game{day.games.length === 1 ? '' : 's'}
                </span>
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {day.games.map((game: any, i: number) => (
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

                    <WinProbBar
                      homeTeam={game.home_team_name?.split(' ').pop() ?? ''}
                      awayTeam={game.away_team_name?.split(' ').pop() ?? ''}
                      homeProb={game.home_win_prob ?? 0.5}
                      awayProb={game.away_win_prob ?? 0.5}
                    />

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
                        <span className="text-gray-500">Proj Pts: </span>
                        <span className="text-white font-semibold">
                          {game.projected_total != null ? Math.round(game.projected_total) : '—'}
                        </span>
                      </div>
                      {game.over_under_line && (
                        <div>
                          <span className="text-gray-500">Line </span>
                          <span className="text-white font-semibold">{game.over_under_line}</span>
                          {game.over_under_rec && (
                            <span
                              className={clsx(
                                'ml-2 text-xs font-bold',
                                game.over_under_rec === 'OVER'
                                  ? 'text-green-400'
                                  : game.over_under_rec === 'UNDER'
                                    ? 'text-red-400'
                                    : 'text-gray-400',
                              )}
                            >
                              {game.over_under_rec}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <div>
        <h2 className="text-xl font-bold text-white mb-1">Top Prop Signals</h2>
        <p className="text-gray-500 text-sm mb-4">Projections where the model diverges most from season averages.</p>

        {betsLoading ? (
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
                <span className="text-gray-400 col-span-2">{bet.season_avg ?? '—'}</span>
                <span
                  className={clsx(
                    'font-bold text-xs',
                    bet.projection > bet.season_avg ? 'text-green-400' : 'text-red-400',
                  )}
                >
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
