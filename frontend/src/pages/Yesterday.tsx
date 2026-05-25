import { useApi } from '../hooks/useApi'
import { predictionsApi } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import clsx from 'clsx'

const STAT_ORDER = ['PTS', 'REB', 'AST', 'FG3M', 'BLK', 'STL']
const STAT_LABEL: Record<string, string> = {
  PTS: 'Points', REB: 'Rebounds', AST: 'Assists',
  FG3M: '3-Pointers Made', BLK: 'Blocks', STL: 'Steals',
}

function StatTable({ rows }: { rows: any[] }) {
  if (!rows.length) return null
  return (
    <div className="bg-surface-card border border-surface-border rounded-xl overflow-hidden mb-3">
      <div className="grid grid-cols-5 gap-1 px-3 py-2 text-xs text-gray-500 uppercase border-b border-surface-border">
        <span className="col-span-2">Player</span>
        <span className="text-right">Avg</span>
        <span className="text-right">Proj</span>
        <span className="text-right">Actual</span>
      </div>
      {rows.map((r, i) => (
        <div key={i} className="grid grid-cols-5 gap-1 px-3 py-2 border-b border-surface-border last:border-0 hover:bg-surface-hover items-center text-sm">
          <span className="col-span-2 text-white font-medium truncate">
            {r.player_name}
            <span className="text-gray-500 font-normal ml-1 text-xs">{r.team_abbreviation}</span>
          </span>
          <span className="text-right text-gray-400">{r.season_avg}</span>
          <span className={clsx('text-right font-semibold', r.predicted_over ? 'text-green-400' : 'text-red-400')}>
            {r.projection}
            <span className="text-xs ml-0.5 opacity-70">{r.predicted_over ? '↑' : '↓'}</span>
          </span>
          <span className="text-right flex items-center justify-end gap-1">
            <span className={clsx('font-bold', r.went_over ? 'text-green-400' : 'text-red-400')}>{r.actual}</span>
            <span>{r.correct ? '✓' : '✗'}</span>
          </span>
        </div>
      ))}
    </div>
  )
}

function TeamColumn({ label, rows }: { label: string; rows: any[] }) {
  return (
    <div className="flex-1 min-w-0">
      <div className="text-sm font-bold text-white mb-3 pb-2 border-b border-surface-border">{label}</div>
      {STAT_ORDER.map(stat => {
        const statRows = rows.filter(r => r.stat === stat)
        if (!statRows.length) return null
        return (
          <div key={stat} className="mb-4">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">{STAT_LABEL[stat]}</div>
            <StatTable rows={statRows} />
          </div>
        )
      })}
    </div>
  )
}

export default function Yesterday() {
  const { data, loading, error } = useApi(() => predictionsApi.getYesterday())
  const rows = (data as any[]) ?? []

  const correct = rows.filter(r => r.correct).length
  const total = rows.length
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0

  // Group by game, then split into away/home
  const gameMap: Record<string, { awayName: string; homeName: string; away: any[]; home: any[] }> = {}
  for (const r of rows) {
    if (!gameMap[r.game]) {
      const [away, home] = r.game.split(' @ ')
      gameMap[r.game] = { awayName: away ?? r.game, homeName: home ?? '', away: [], home: [] }
    }
    if (r.is_home) gameMap[r.game].home.push(r)
    else gameMap[r.game].away.push(r)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Settled Games</h1>
        <p className="text-gray-500 text-sm">How the model's projections compared to actual player stats from the most recently completed games.</p>
      </div>

      {loading ? (
        <LoadingSpinner label="Loading settled game results..." />
      ) : error ? (
        <div className="bg-surface-card border border-red-900 rounded-xl p-8 text-center text-red-400">
          {error}
        </div>
      ) : rows.length === 0 ? (
        <div className="bg-surface-card border border-surface-border rounded-xl p-8 text-center text-gray-500">
          No completed games found.
        </div>
      ) : (
        <>
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

          {Object.entries(gameMap).map(([game, { awayName, homeName, away, home }]) => (
            <div key={game}>
              <h2 className="text-lg font-bold text-white mb-4">{game}</h2>
              <div className="flex gap-6">
                <TeamColumn label={`${awayName} (Away)`} rows={away} />
                <div className="w-px bg-surface-border shrink-0" />
                <TeamColumn label={`${homeName} (Home)`} rows={home} />
              </div>
            </div>
          ))}

          <div className="text-xs text-gray-600 text-center">
            Correct = projection and actual were on the same side of the season average.
          </div>
        </>
      )}
    </div>
  )
}
