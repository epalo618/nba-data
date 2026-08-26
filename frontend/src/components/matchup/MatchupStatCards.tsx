import StatCard from '../StatCard'
import { Sport } from '../../services/api'
import { MATCHUP_SUMMARY_CARDS } from '../../config/statColumns'

interface Props {
  sport: Sport
  team: any
}

// The last-10-games line chart in GameMatchup.tsx is already generic (every
// sport's get_team_last_n_games returns PTS/PTS_ALLOWED) — these summary cards
// are driven by MATCHUP_SUMMARY_CARDS (statColumns.ts) the same way every other
// stat table in the app is, so a new sport only needs a registry entry here,
// not a new branch in this component.
export default function MatchupStatCards({ sport, team }: Props) {
  const cards = MATCHUP_SUMMARY_CARDS[sport]
  return (
    <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
      {cards.map(c => (
        <StatCard key={c.key} label={c.label} value={team?.[c.key]?.toFixed(c.decimals ?? 1) ?? '—'} />
      ))}
    </div>
  )
}
