import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import SportSwitcher from './SportSwitcher'
import { useCurrentSport } from '../hooks/useCurrentSport'

const SUBLINKS = [
  { to: '', label: 'Dashboard' },
  { to: '/games', label: 'Games' },
  { to: '/teams', label: 'Teams' },
  { to: '/players', label: 'Players' },
  { to: '/predictions', label: 'Best Bets' },
  { to: '/yesterday', label: 'Settled Games' },
]

export default function Navbar() {
  const { sport: s } = useCurrentSport()
  const base = `/${s}`

  return (
    <nav className="bg-surface-card border-b border-surface-border sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 flex items-center h-14 gap-6">
        <span className="text-brand font-bold text-lg tracking-wide mr-4">Sports Analytics</span>
        <SportSwitcher />
        {SUBLINKS.map(l => (
          <NavLink
            key={l.to}
            to={`${base}${l.to}`}
            end={l.to === ''}
            className={({ isActive }) =>
              clsx('text-sm font-medium transition-colors', isActive ? 'text-brand' : 'text-gray-400 hover:text-white')
            }
          >
            {l.label}
          </NavLink>
        ))}
        <span className="ml-auto text-xs text-gray-600">Betting is never guaranteed. Use data responsibly.</span>
      </div>
    </nav>
  )
}
