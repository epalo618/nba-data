import { useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { gamesApi, predictionsApi, teamsApi } from '../services/api'
import WinProbBar from '../components/WinProbBar'
import PlayerPropRow from '../components/PlayerPropRow'
import LoadingSpinner from '../components/LoadingSpinner'
import StatCard from '../components/StatCard'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

export default function GameMatchup() {
  const { homeId, awayId } = useParams<{ homeId: string; awayId: string }>()
  const hId = Number(homeId)
  const aId = Number(awayId)

  const { data: matchup, loading: mLoading } = useApi(() => gamesApi.getMatchup(hId, aId), [hId, aId])
  const { data: playerProjs, loading: pLoading } = useApi(
    () => predictionsApi.getGamePlayerProjections(hId, aId, 8),
    [hId, aId]
  )
  const { data: allTeamStats } = useApi(() => teamsApi.getStats())

  const m = matchup as any
  const pp = playerProjs as any

  const teamMap = ((allTeamStats as any[]) ?? []).reduce((acc: any, t: any) => {
    acc[t.TEAM_ID] = t
    return acc
  }, {})

  const homeTeam = teamMap[hId]
  const awayTeam = teamMap[aId]

  const homeChartData = (m?.home_last10?.pts ?? []).map((pts: number, i: number) => ({
    game: `G${10 - i}`,
    pts,
    allowed: m?.home_last10?.pts_allowed?.[i] ?? 0,
  })).reverse()

  const awayChartData = (m?.away_last10?.pts ?? []).map((pts: number, i: number) => ({
    game: `G${10 - i}`,
    pts,
    allowed: m?.away_last10?.pts_allowed?.[i] ?? 0,
  })).reverse()

  if (mLoading) return <LoadingSpinner label="Loading matchup..." />

  const winProb = m?.win_probability ?? {}
  const homeName = homeTeam?.TEAM_NAME ?? `Team ${hId}`
  const awayName = awayTeam?.TEAM_NAME ?? `Team ${aId}`

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      <div className="bg-surface-card border border-surface-border rounded-xl p-6">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-white">{homeName} <span className="text-gray-500">vs</span> {awayName}</h1>
          <p className="text-gray-500 text-sm mt-1">Game Day Matchup Analysis</p>
        </div>
        <WinProbBar
          homeTeam={homeName}
          awayTeam={awayName}
          homeProb={winProb.home_win_prob ?? 0.5}
          awayProb={winProb.away_win_prob ?? 0.5}
        />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          <StatCard label="Projected Total" value={m?.projected_total ?? '—'} />
          <StatCard label="Home Win Prob" value={`${Math.round((winProb.home_win_prob ?? 0.5) * 100)}%`} color="text-brand" />
          <StatCard label="Away Win Prob" value={`${Math.round((winProb.away_win_prob ?? 0.5) * 100)}%`} color="text-brand" />
          <StatCard
            label="Projected Winner"
            value={winProb.favored_team ?? ((winProb.home_win_prob ?? 0.5) >= 0.5 ? homeName.split(' ').pop()! : awayName.split(' ').pop()!)}
            color="text-green-400"
          />
        </div>

        {winProb.reasons?.length > 0 && (
          <div className="mt-5 border-t border-surface-border pt-5">
            <div className="text-xs text-brand font-semibold uppercase tracking-wide mb-2">
              Why {winProb.favored_team} is favored
            </div>
            <ul className="space-y-1.5">
              {winProb.reasons.map((r: string, i: number) => (
                <li key={i} className="text-sm text-gray-300 flex gap-2">
                  <span className="text-brand font-bold mt-0.5">›</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[{ team: homeTeam, name: homeName, chart: homeChartData }, { team: awayTeam, name: awayName, chart: awayChartData }].map(({ team, name, chart }) => (
          <div key={name} className="bg-surface-card border border-surface-border rounded-xl p-5">
            <h2 className="text-white font-bold mb-3">{name} — Last 10 Games</h2>
            <div className="grid grid-cols-3 gap-3 mb-4 text-sm">
              <StatCard label="PTS/G" value={team?.PTS?.toFixed(1) ?? '—'} />
              <StatCard label="OFF RTG" value={team?.OFF_RATING?.toFixed(1) ?? '—'} />
              <StatCard label="DEF RTG" value={team?.DEF_RATING?.toFixed(1) ?? '—'} />
            </div>
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={chart}>
                <XAxis dataKey="game" tick={{ fill: '#6B7280', fontSize: 11 }} />
                <YAxis domain={['auto', 'auto']} tick={{ fill: '#6B7280', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#21252E', border: '1px solid #2E3340', color: '#E5E7EB' }} />
                <ReferenceLine y={team?.PTS ?? 110} stroke="#C9A84C" strokeDasharray="3 3" />
                <Line type="monotone" dataKey="pts" stroke="#C9A84C" dot={false} strokeWidth={2} name="Pts Scored" />
                <Line type="monotone" dataKey="allowed" stroke="#6B7280" dot={false} strokeWidth={1.5} name="Pts Allowed" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>

      <div>
        <h2 className="text-xl font-bold text-white mb-4">Player Prop Projections</h2>
        {pLoading ? <LoadingSpinner label="Projecting player props..." /> : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { label: homeName, players: pp?.home_players ?? [] },
              { label: awayName, players: pp?.away_players ?? [] },
            ].map(({ label, players }) => (
              <div key={label} className="bg-surface-card border border-surface-border rounded-xl p-5">
                <h3 className="text-white font-semibold mb-3">{label}</h3>
                {players.map((p: any) => (
                  <div key={p.player_id} className="mb-5">
                    <div className="text-sm font-bold text-brand mb-1">{p.player_name}</div>
                    <div className="grid grid-cols-8 gap-2 text-xs text-gray-600 mb-1 px-0">
                      <span>STAT</span>
                      <span>REG</span>
                      <span className="text-yellow-700">POST</span>
                      <span>L10</span>
                      <span>L5</span>
                      <span className="font-semibold text-gray-400">PROJ</span>
                      <span>LINE</span>
                      <span>SIGNAL</span>
                    </div>
                    {(p.projections ?? []).map((proj: any) => (
                      <PlayerPropRow key={proj.stat} proj={proj} />
                    ))}
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="text-xs text-gray-600 text-center">
        All projections are model-based estimates. Past performance does not guarantee future results. Bet responsibly.
      </div>
    </div>
  )
}
