interface Props {
  homeTeam: string
  awayTeam: string
  homeProb: number
  drawProb: number
  awayProb: number
}

export default function WinProbBar3Way({ homeTeam, awayTeam, homeProb, drawProb, awayProb }: Props) {
  const homePct = Math.round(homeProb * 100)
  const drawPct = Math.round(drawProb * 100)
  const awayPct = Math.round(awayProb * 100)

  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-semibold text-white">{awayTeam} <span className="text-brand">{awayPct}%</span></span>
        <span className="font-semibold text-gray-400">Draw <span className="text-brand">{drawPct}%</span></span>
        <span className="font-semibold text-white"><span className="text-brand">{homePct}%</span> {homeTeam}</span>
      </div>
      <div className="h-3 flex rounded-full overflow-hidden">
        <div className="bg-brand transition-all" style={{ width: `${awayPct}%` }} />
        <div className="bg-gray-500 transition-all" style={{ width: `${drawPct}%` }} />
        <div className="bg-blue-400 transition-all" style={{ width: `${homePct}%` }} />
      </div>
    </div>
  )
}
