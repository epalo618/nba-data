import StatCard from '../StatCard'
import { Sport } from '../../services/api'

interface Props {
  sport: Sport
  team: any
}

// The last-10-games line chart in GameMatchup.tsx is already generic (every
// sport's get_team_last_n_games returns PTS/PTS_ALLOWED) — only these summary
// cards need sport-specific fields, so this stays one small component rather
// than two near-duplicate NBAMatchupStats/NFLMatchupStats files.
export default function MatchupStatCards({ sport, team }: Props) {
  if (sport === 'nfl') {
    return (
      <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
        <StatCard label="PPG" value={team?.PTS?.toFixed(1) ?? '—'} />
        <StatCard label="PAPG" value={team?.PTS_ALLOWED?.toFixed(1) ?? '—'} />
        <StatCard label="YDS/G" value={team?.YDS_PER_GAME?.toFixed(1) ?? '—'} />
      </div>
    )
  }
  return (
    <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
      <StatCard label="PTS/G" value={team?.PTS?.toFixed(1) ?? '—'} />
      <StatCard label="OFF RTG" value={team?.OFF_RATING?.toFixed(1) ?? '—'} />
      <StatCard label="DEF RTG" value={team?.DEF_RATING?.toFixed(1) ?? '—'} />
    </div>
  )
}
