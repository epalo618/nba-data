import clsx from 'clsx'
import ConfidenceBadge from './ConfidenceBadge'

interface Projection {
  stat: string
  season_avg: number
  reg_season_avg?: number
  playoff_avg?: number | null
  last5_avg: number
  last10_avg: number
  projection: number
  line?: number
  recommendation?: string
  confidence?: string
  opponent_rank: number
}

export default function PlayerPropRow({ proj }: { proj: Projection }) {
  const diff = proj.line != null ? proj.projection - proj.line : null
  const rec = proj.recommendation ?? (diff != null ? (diff > 0 ? 'OVER' : 'UNDER') : null)

  return (
    <div className="grid grid-cols-8 gap-2 items-center py-2 border-b border-surface-border text-sm">
      <span className="text-gray-400 uppercase font-semibold">{proj.stat}</span>
      <span className="text-gray-300">{proj.reg_season_avg ?? proj.season_avg}</span>
      <span className={clsx(proj.playoff_avg != null ? 'text-yellow-400' : 'text-gray-600')}>
        {proj.playoff_avg != null ? proj.playoff_avg : '—'}
      </span>
      <span className="text-gray-300">{proj.last10_avg}</span>
      <span className="text-gray-300">{proj.last5_avg}</span>
      <span className="font-bold text-white">{proj.projection}</span>
      <span className="text-gray-500">{proj.line ?? '—'}</span>
      <div className="flex items-center gap-2">
        {rec && (
          <span className={clsx('font-bold text-xs', rec === 'OVER' ? 'text-green-400' : rec === 'UNDER' ? 'text-red-400' : 'text-gray-400')}>
            {rec}
          </span>
        )}
        {proj.confidence && <ConfidenceBadge label={proj.confidence} />}
      </div>
    </div>
  )
}
