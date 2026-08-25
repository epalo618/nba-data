import { useNavigate, useParams } from 'react-router-dom'
import { useEffect } from 'react'
import { Sport } from '../services/api'

const SPORTS: { key: Sport; label: string }[] = [
  { key: 'nba', label: 'NBA' },
  { key: 'nfl', label: 'NFL' },
  { key: 'soccer', label: 'Soccer' },
]

// Mirrors backend/app/services/sports_registry.py's SOCCER_LEAGUES keys/names.
const SOCCER_LEAGUES = [
  { key: 'epl', label: 'Premier League' },
  { key: 'laliga', label: 'La Liga' },
  { key: 'seriea', label: 'Serie A' },
  { key: 'bundesliga', label: 'Bundesliga' },
  { key: 'ligue1', label: 'Ligue 1' },
  { key: 'ucl', label: 'Champions League' },
  { key: 'uel', label: 'Europa League' },
  { key: 'mls', label: 'MLS' },
]

export default function SportSwitcher() {
  const { sport, league } = useParams<{ sport: Sport; league: string }>()
  const navigate = useNavigate()
  const s = (sport ?? 'nba') as Sport

  useEffect(() => {
    if (sport) localStorage.setItem('lastSport', sport)
  }, [sport])

  const handleSportChange = (next: Sport) => {
    if (next === 'soccer') {
      navigate(`/soccer/${localStorage.getItem('lastSoccerLeague') ?? 'epl'}`)
    } else {
      navigate(`/${next}`)
    }
  }

  const handleLeagueChange = (next: string) => {
    localStorage.setItem('lastSoccerLeague', next)
    navigate(`/soccer/${next}`)
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
      {s === 'soccer' && (
        <select
          value={league ?? 'epl'}
          onChange={e => handleLeagueChange(e.target.value)}
          className="bg-surface border border-surface-border rounded-lg px-2 py-1.5 text-sm text-white focus:outline-none focus:border-brand"
        >
          {SOCCER_LEAGUES.map(l => (
            <option key={l.key} value={l.key}>{l.label}</option>
          ))}
        </select>
      )}
    </div>
  )
}
