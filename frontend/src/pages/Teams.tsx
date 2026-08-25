import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { teamsApi, Sport } from '../services/api'
import { TEAM_COLUMNS } from '../config/statColumns'
import SortableStatTable from '../components/SortableStatTable'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Teams() {
  const { sport } = useParams<{ sport: Sport }>()
  const s = (sport ?? 'nba') as Sport
  const COLS = TEAM_COLUMNS[s]
  const { data, loading } = useApi(() => teamsApi.getStats(s), [s])
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

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">All 30 Teams</h1>
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
        <div className="bg-surface-card border border-surface-border rounded-xl overflow-auto">
          <SortableStatTable
            rows={teams}
            columns={COLS}
            rowKey={t => t.TEAM_ID}
            leadingColumns={[{ label: 'Team', render: t => <span className="text-white font-medium">{t.TEAM_NAME}</span> }]}
            sort={sort}
            asc={asc}
            onSort={handleSort}
          />
        </div>
      )}
    </div>
  )
}
