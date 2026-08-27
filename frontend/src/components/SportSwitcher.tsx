import { useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { Sport } from '../services/api'
import { useCurrentSport } from '../hooks/useCurrentSport'

const SPORTS: { key: Sport; label: string }[] = [
  { key: 'nba', label: 'NBA' },
  { key: 'nfl', label: 'NFL' },
]

export default function SportSwitcher() {
  const { sport: s } = useCurrentSport()
  const navigate = useNavigate()

  useEffect(() => {
    localStorage.setItem('lastSport', s)
  }, [s])

  const handleSportChange = (next: Sport) => {
    navigate(`/${next}`)
  }

  return (
    <div className="flex items-center gap-2">
      <select
        value={s}
        onChange={e => handleSportChange(e.target.value as Sport)}
        className="bg-surface border border-surface-border rounded-lg px-2 py-1.5 text-sm text-white focus:outline-none focus:border-brand"
      >
        {SPORTS.map(sp => (
          <option key={sp.key} value={sp.key}>{sp.label}</option>
        ))}
      </select>
    </div>
  )
}
