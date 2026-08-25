import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { playersApi, Sport } from '../services/api'
import { PLAYER_COLUMNS, DEFAULT_PLAYER_SORT } from '../config/statColumns'
import SortableStatTable from '../components/SortableStatTable'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Players() {
  const { sport } = useParams<{ sport: Sport }>()
  const s = (sport ?? 'nba') as Sport
  const COLS = PLAYER_COLUMNS[s]
  const { data, loading } = useApi(() => playersApi.getStats(s), [s])
  const [sort, setSort] = useState<string>(DEFAULT_PLAYER_SORT[s])
  const [asc, setAsc] = useState(false)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 50

  const players = ((data as any[]) ?? [])
    .filter(p =>
      p.PLAYER_NAME?.toLowerCase().includes(search.toLowerCase()) ||
      p.TEAM_ABBREVIATION?.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => {
      const va = a[sort] ?? 0
      const vb = b[sort] ?? 0
      return asc ? va - vb : vb - va
    })

  const paginated = players.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const totalPages = Math.ceil(players.length / PAGE_SIZE)

  const handleSort = (key: string) => {
    if (sort === key) setAsc(!asc)
    else { setSort(key); setAsc(false) }
    setPage(0)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">All Players</h1>
        <input
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0) }}
          placeholder="Search player or team..."
          className="bg-surface-card border border-surface-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 w-56 focus:outline-none focus:border-brand"
        />
      </div>

      {loading ? (
        <LoadingSpinner label="Loading player stats..." />
      ) : (
        <>
          <div className="bg-surface-card border border-surface-border rounded-xl overflow-auto">
            <SortableStatTable
              rows={paginated}
              columns={COLS}
              rowKey={p => p.PLAYER_ID}
              leadingColumns={[
                { label: 'Player', render: p => <span className="text-white font-medium">{p.PLAYER_NAME}</span> },
                { label: 'Team', render: p => p.TEAM_ABBREVIATION },
              ]}
              sort={sort}
              asc={asc}
              onSort={handleSort}
            />
          </div>

          <div className="flex justify-between items-center mt-4 text-sm text-gray-500">
            <span>{players.length} players</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1 bg-surface-card border border-surface-border rounded disabled:opacity-30 hover:border-brand"
              >
                Prev
              </button>
              <span className="px-2 py-1">{page + 1} / {totalPages}</span>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-3 py-1 bg-surface-card border border-surface-border rounded disabled:opacity-30 hover:border-brand"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
