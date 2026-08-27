import { useLocation } from 'react-router-dom'
import { Sport } from '../services/api'

// Navbar/SportSwitcher render as siblings of <Routes> in App.tsx, not as
// descendants of the matched <Route>, so useParams() always returns {} there —
// only components rendered inside a Route's `element` get route params.
// Parsing the URL directly via useLocation works regardless of nesting.
export function useCurrentSport(): { sport: Sport } {
  const { pathname } = useLocation()
  const segments = pathname.split('/').filter(Boolean)
  const sport = (segments[0] || 'nba') as Sport
  return { sport }
}
