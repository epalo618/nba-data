import { useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { predictionsApi, Sport } from '../services/api'
import { PREDICTION_STAT_CATEGORIES } from '../config/statColumns'
import LoadingSpinner from '../components/LoadingSpinner'
import ConfidenceBadge from '../components/ConfidenceBadge'
import clsx from 'clsx'

export default function Predictions() {
  const { sport } = useParams<{ sport: Sport }>()
  const s = (sport ?? 'nba') as Sport
  const { data, loading } = useApi(() => predictionsApi.getBestBets(s), [s])
  const bets = (data as any[]) ?? []

  const categories = PREDICTION_STAT_CATEGORIES[s].map(cat => ({
    label: cat.label,
    bets: bets.filter(b => b.stat === cat.key),
  }))

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white mb-1">Best Bets Today</h1>
        <p className="text-gray-500 text-sm">
          Model projections ranked by divergence from season average. Higher divergence = stronger signal.
        </p>
        <div className="mt-2 text-xs text-yellow-600 bg-yellow-950 border border-yellow-900 rounded-lg px-3 py-2 inline-block">
          These are statistical projections only. Always bet responsibly and within your means.
        </div>
      </div>

      {loading ? (
        <LoadingSpinner label="Calculating today's best bets..." />
      ) : (
        <div className="space-y-8">
          {categories.map(({ label, bets: catBets }) => (
            <div key={label}>
              <h2 className="text-lg font-bold text-white mb-3">{label}</h2>
              <div className="bg-surface-card border border-surface-border rounded-xl overflow-hidden">
                <div className="grid grid-cols-9 gap-2 px-4 py-2 text-xs text-gray-500 uppercase border-b border-surface-border">
                  <span className="col-span-2">Player</span>
                  <span>Team</span>
                  <span className="text-right">Reg Avg</span>
                  <span className="text-right text-yellow-600">Post Avg</span>
                  <span className="text-right">L10</span>
                  <span className="text-right">Projection</span>
                  <span className="text-right">Tot Avg</span>
                  <span className="text-right">Signal</span>
                </div>
                {catBets.slice(0, 10).map((bet: any, i: number) => {
                  const isOver = bet.projection > bet.season_avg
                  const diffPct = Math.abs((bet.projection - bet.season_avg) / Math.max(bet.season_avg, 1)) * 100
                  const conf = diffPct > 15 ? 'STRONG' : diffPct > 10 ? 'HIGH' : diffPct > 5 ? 'MED' : 'LOW'
                  return (
                    <div key={i} className="grid grid-cols-9 gap-2 px-4 py-3 border-b border-surface-border hover:bg-surface-hover items-center">
                      <span className="col-span-2 text-white font-medium text-sm">{bet.player_name}</span>
                      <span className="text-gray-400 text-sm">{bet.team_abbreviation}</span>
                      <span className="text-right text-gray-400 text-sm">{bet.reg_season_avg ?? bet.season_avg}</span>
                      <span className="text-right text-yellow-400 text-sm">{bet.playoff_avg ?? '—'}</span>
                      <span className="text-right text-gray-400 text-sm">{bet.last10_avg}</span>
                      <span className="text-right text-white font-bold">{bet.projection}</span>
                      <span className="text-right text-gray-500 text-sm">{bet.season_avg ?? '—'}</span>
                      <div className="flex justify-end items-center gap-2">
                        <span className={clsx('text-xs font-bold', isOver ? 'text-green-400' : 'text-red-400')}>
                          {isOver ? '↑ OVER' : '↓ UNDER'}
                        </span>
                        <ConfidenceBadge label={conf} />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
