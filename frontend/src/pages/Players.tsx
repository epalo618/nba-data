import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { playersApi } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { Link } from 'react-router-dom'

const COLS = [
  { key: 'GP', label: 'GP' },
  { key: 'MIN', label: 'MIN' },
  { key: 'PTS', label: 'PTS' },
  { key: 'REB', label: 'REB' },
  { key: 'AST', label: 'AST' },
  { key: 'STL', label: 'STL' },
  { key: 'BLK', label: 'BLK' },
  { key: 'TOV', label: 'TOV' },
  { key: 'FG_PCT', label: 'FG%' },
  { key: 'FG3_PCT', label: '3P%' },
  { key: 'FT_PCT', label: 'FT%' },
  { key: 'PLUS_MINUS', label: '+/-' },
]

export default function Players() {
  const { data, loading } = useApi(() => playersApi.getStats())
  const [sort, setSort] = useState<string>('PTS')
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
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border">
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Player</th>
                  <th className="text-left px-3 py-3 text-gray-500 font-medium">Team</th>
                  {COLS.map(c => (
                    <th
                      key={c.key}
                      className="px-3 py-3 text-gray-500 font-medium cursor-pointer hover:text-white text-right"
                      onClick={() => handleSort(c.key)}
                    >
                      {c.label} {sort === c.key ? (asc ? '↑' : '↓') : ''}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paginated.map((p: any) => (
                  <tr key={p.PLAYER_ID} className="border-b border-surface-border hover:bg-surface-hover">
                    <td className="px-4 py-2">
                      <Link to={`/players/${p.PLAYER_ID}`} className="text-white font-medium hover:text-brand">
                        {p.PLAYER_NAME}
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-gray-400">{p.TEAM_ABBREVIATION}</td>
                    {COLS.map(c => (
                      <td key={c.key} className="px-3 py-2 text-right text-gray-300">
                        {c.key.includes('PCT') ? ((p[c.key] ?? 0) * 100).toFixed(1) + '%' :
                         c.key === 'PLUS_MINUS' ? (
                           <span className={p[c.key] > 0 ? 'text-green-400' : p[c.key] < 0 ? 'text-red-400' : 'text-gray-400'}>
                             {p[c.key]?.toFixed(1)}
                           </span>
                         ) : p[c.key]?.toFixed ? p[c.key].toFixed(1) : p[c.key] ?? '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
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
