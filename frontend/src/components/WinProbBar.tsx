interface Props {
  homeTeam: string
  awayTeam: string
  homeProb: number
  awayProb: number
}

export default function WinProbBar({ homeTeam, awayTeam, homeProb, awayProb }: Props) {
  const homePct = Math.round(homeProb * 100)
  const awayPct = Math.round(awayProb * 100)

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-semibold text-white">{homeTeam} <span className="text-brand">{homePct}%</span></span>
        <span className="font-semibold text-white"><span className="text-brand">{awayPct}%</span> {awayTeam}</span>
      </div>
      <div className="h-3 flex rounded-full overflow-hidden">
        <div className="bg-brand transition-all" style={{ width: `${homePct}%` }} />
        <div className="bg-surface-border flex-1" />
      </div>
    </div>
  )
}
