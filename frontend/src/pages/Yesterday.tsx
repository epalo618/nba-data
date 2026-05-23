import { useApi } from '../hooks/useApi'
import { predictionsApi } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import clsx from 'clsx'

const STAT_ORDER = ['PTS', 'REB', 'AST', 'FG3M', 'BLK', 'STL']
const STAT_LABEL: Record<string, string> = {
  PTS: 'Points', REB: 'Rebounds', AST: 'Assists',
  FG3M: '3-Pointers Made', BLK: 'Blocks', STL: 'Steals',
}

export default function Yesterday() {
  const { data, loading, error } = useApi(() => predictionsApi.getYesterday())
  const rows = (data as any[]) ?? []

  const correct = rows.filter(r => r.correct).length
  const total = rows.length
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0

  const byGame = rows.reduce((acc: Record<string, any[]>, r) => {
    acc[r.game] = acc[r.game] ?? []
    acc[r.game].push(r)
    return acc
  }, {})

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Yesterday's Results</h1>
        <p className="text-gray-500 text-sm">How the model's projections compared to actual player stats.</p>
      </div>

      {loading ? (
        <LoadingSpinner label="Loading yesterday's results..." />
      ) : error ? (
        <div className="bg-surface-card border border-red-900 rounded-xl p-8 text-center text-red-400">
          {error}
        </div>
      ) : rows.length === 0 ? (
        <div className="bg-surface-card border border-surface-border rounded-xl p-8 text-center text-gray-500">
          No completed games found for yesterday.
        </div>
      ) : (
        <>
          {/* Summary */}
          <div className="flex gap-6 flex-wrap">
            <div className="bg-surface-card border border-surface-border rounded-xl px-6 py-4 text-center">
              <div className="text-3xl font-bold text-green-400">{correct}</div>
              <div className="text-xs text-gray-500 mt-1">Correct</div>
            </div>
            <div className="bg-surface-card border border-surface-border rounded-xl px-6 py-4 text-center">
              <div className="text-3xl font-bold text-red-400">{total - correct}</div>
              <div className="text-xs text-gray-500 mt-1">Incorrect</div>
            </div>
            <div className="bg-surface-card border border-surface-border rounded-xl px-6 py-4 text-center">
              <div className={clsx('text-3xl font-bold', pct >= 55 ? 'text-green-400' : pct >= 45 ? 'text-yellow-400' : 'text-red-400')}>
                {pct}%
              </div>
              <div className="text-xs text-gray-500 mt-1">Accuracy</div>
            </div>
          </div>

          {/* Per-game tables */}
          {Object.entries(byGame).map(([game, gameRows]) => (
            <div key={game}>
              <h2 className="text-lg font-bold text-white mb-3">{game}</h2>
              {STAT_ORDER.map(stat => {
                const statRows = gameRows.filter(r => r.stat === stat)
                if (!statRows.length) return null
                return (
                  <div key={stat} className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">{STAT_LABEL[stat]}</h3>
                    <div className="bg-surface-card border border-surface-border rounded-xl overflow-hidden">
                      <div className="grid grid-cols-6 gap-2 px-4 py-2 text-xs text-gray-500 uppercase border-b border-surface-border">
                        <span className="col-span-2">Player</span>
                        <span className="text-right">Season Avg</span>
                        <span className="text-right">Projected</span>
                        <span className="text-right">Actual</span>
                        <span className="text-right">Result</span>
                      </div>
                      {statRows.map((r, i) => (
                        <div key={i} className="grid grid-cols-6 gap-2 px-4 py-3 border-b border-surface-border hover:bg-surface-hover items-center text-sm">
                          <span className="col-span-2 text-white font-medium">
                            {r.player_name}
                            <span className="text-gray-500 font-normal ml-1 text-xs">{r.team_abbreviation}</span>
                          </span>
                          <span className="text-right text-gray-400">{r.season_avg}</span>
                          <span className={clsx('text-right font-semibold', r.predicted_over ? 'text-green-400' : 'text-red-400')}>
                            {r.projection}
                            <span className="text-xs ml-1 opacity-70">{r.predicted_over ? '↑' : '↓'}</span>
                          </span>
                          <span className={clsx('text-right font-bold', r.went_over ? 'text-green-400' : 'text-red-400')}>
                            {r.actual}
                          </span>
                          <div className="flex justify-end">
                            {r.correct ? (
                              <span className="text-green-400 font-bold text-base">✓</span>
                            ) : (
                              <span className="text-red-400 font-bold text-base">✗</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          ))}
        </>
      )}

      <div className="text-xs text-gray-600 text-center">
        Correct = projection and actual were on the same side of the season average.
      </div>
    </div>
  )
}
