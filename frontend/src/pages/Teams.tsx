import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { teamsApi } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const COLS = [
  { key: 'W', label: 'W' },
  { key: 'L', label: 'L' },
  { key: 'W_PCT', label: 'WIN%' },
  { key: 'PTS', label: 'PTS' },
  { key: 'REB', label: 'REB' },
  { key: 'AST', label: 'AST' },
  { key: 'STL', label: 'STL' },
  { key: 'BLK', label: 'BLK' },
  { key: 'TOV', label: 'TOV' },
  { key: 'OFF_RATING', label: 'ORTG' },
  { key: 'DEF_RATING', label: 'DRTG' },
  { key: 'NET_RATING', label: 'NET' },
  { key: 'PACE', label: 'PACE' },
]

export default function Teams() {
  const { data, loading } = useApi(() => teamsApi.getStats())
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
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border">
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Team</th>
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
              {teams.map((t: any) => (
                <tr key={t.TEAM_ID} className="border-b border-surface-border hover:bg-surface-hover">
                  <td className="px-4 py-3">
                    <span className="text-white font-medium">{t.TEAM_NAME}</span>
                  </td>
                  {COLS.map(c => (
                    <td key={c.key} className="px-3 py-3 text-right text-gray-300">
                      {c.key === 'W_PCT' ? (t[c.key] * 100).toFixed(1) + '%' :
                       c.key === 'NET_RATING' ? (
                         <span className={t[c.key] > 0 ? 'text-green-400' : 'text-red-400'}>
                           {t[c.key]?.toFixed(1)}
                         </span>
                       ) : t[c.key]?.toFixed ? t[c.key].toFixed(1) : t[c.key] ?? '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
