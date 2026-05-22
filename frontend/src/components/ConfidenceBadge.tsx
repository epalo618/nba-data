import clsx from 'clsx'

const styles: Record<string, string> = {
  STRONG: 'bg-green-900 text-green-300 border-green-700',
  HIGH: 'bg-emerald-900 text-emerald-300 border-emerald-700',
  MED: 'bg-yellow-900 text-yellow-300 border-yellow-700',
  LOW: 'bg-gray-800 text-gray-400 border-gray-600',
  LEAN: 'bg-gray-800 text-gray-400 border-gray-600',
}

export default function ConfidenceBadge({ label }: { label: string }) {
  return (
    <span className={clsx('text-xs px-2 py-0.5 rounded border font-semibold', styles[label] ?? styles.LOW)}>
      {label}
    </span>
  )
}
