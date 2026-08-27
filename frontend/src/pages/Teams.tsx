import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { teamsApi } from '../services/api'
import { useCurrentSport } from '../hooks/useCurrentSport'
import { TEAM_COLUMNS } from '../config/statColumns'
import SortableStatTable from '../components/SortableStatTable'
import LoadingSpinner from '../components/LoadingSpinner'

// Display order for the separate per-league tables shown under "All Leagues" —
// mirrors SportSwitcher.tsx's SOCCER_LEAGUES order.
const LEAGUE_ORDER = ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'Champions League']

export default function Teams() {
  const { sport: s, league } = useCurrentSport()
  const COLS = TEAM_COLUMNS[s]
  const { data, loading } = useApi(() => teamsApi.getStats(s, league), [s, league])
  const [sort, setSort] = useState<string>('W_PCT')
  const [asc, setAsc] = useState(false)
  const [search, setSearch] = useState('')

  const teams = ((data as any[]) ?? [])
    .filter(t => t.TEAM_NAME?.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      const va = a[sort] ?? 0
      const vb = b[sort] ?? 0
      return asc ? va - vb : vb - va
    })

  const handleSort = (key: string) => {
    if (sort === key) setAsc(!asc)
    else { setSort(key); setAsc(false) }
  }

  const leadingColumns = [{ label: 'Team', render: (t: any) => <span className="text-white font-medium">{t.TEAM_NAME}</span> }]

  // "All Leagues" mixes standings from 6 separate competitions — a single
  // merged table sorted by points reads as one confusing league table, so
  // split it into one table per competition instead.
  const isAllLeagues = s === 'soccer' && league === 'all'
  const groups: [string, any[]][] = isAllLeagues
    ? LEAGUE_ORDER
        .map((lg): [string, any[]] => [lg, teams.filter(t => t.LEAGUE === lg)])
        .filter(([, rows]) => rows.length > 0)
    : [['', teams]]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">{(data as any[])?.length ? `All ${(data as any[]).length} Teams` : 'Teams'}</h1>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search team..."
          className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 w-48 focus:outline-none focus:border-brand"
        />
      </div>

      {loading ? (
        <LoadingSpinner label="Loading team stats..." />
      ) : (
        <div className="space-y-8">
          {groups.map(([label, rows]) => (
            <div key={label || 'single'}>
              {label && <h2 className="text-lg font-bold text-white mb-3">{label}</h2>}
              <div className="bg-surface-card border border-surface-border rounded-xl overflow-auto">
                <SortableStatTable
                  rows={rows}
                  columns={COLS}
                  rowKey={t => `${t.TEAM_ID}_${t.LEAGUE ?? ''}`}
                  leadingColumns={leadingColumns}
                  sort={sort}
                  asc={asc}
                  onSort={handleSort}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
