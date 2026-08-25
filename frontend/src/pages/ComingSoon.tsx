import { useParams } from 'react-router-dom'
import { Sport } from '../services/api'
import { SPORT_LABEL } from '../types/domain'

export default function ComingSoon() {
  // The /nfl/* routes carry no :sport param (literal path), and /soccer/:league/*
  // routes carry :league but not :sport — so resolve which sport this is from
  // whichever param is actually present, defaulting to nfl when neither is.
  const { sport, league } = useParams<{ sport?: Sport; league?: string }>()
  const resolvedSport: Sport = sport ?? (league ? 'soccer' : 'nfl')
  const label = SPORT_LABEL[resolvedSport]

  return (
    <div className="max-w-2xl mx-auto px-4 py-24 text-center">
      <h1 className="text-2xl font-bold text-white mb-2">{label} is coming soon</h1>
      <p className="text-gray-500 text-sm">
        We're still wiring up data and predictions for {label}. Check back soon.
      </p>
    </div>
  )
}
