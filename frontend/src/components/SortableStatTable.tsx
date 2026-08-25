import clsx from 'clsx'
import type { ReactNode } from 'react'
import { ColumnConfig } from '../config/statColumns'

function formatCell(row: any, col: ColumnConfig) {
  const v = row[col.key]
  if (v === undefined || v === null) return '—'
  const decimals = col.decimals ?? 1
  if (col.percent) return ((v as number) * 100).toFixed(decimals) + '%'
  if (col.signColor) {
    return (
      <span className={v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-gray-400'}>
        {(v as number).toFixed(decimals)}
      </span>
    )
  }
  return typeof v === 'number' ? v.toFixed(decimals) : v
}

interface LeadingColumn {
  label: string
  render: (row: any) => ReactNode
}

interface Props {
  rows: any[]
  columns: ColumnConfig[]
  rowKey: (row: any) => string | number
  leadingColumns: LeadingColumn[]
  sort: string
  asc: boolean
  onSort: (key: string) => void
}

export default function SortableStatTable({ rows, columns, rowKey, leadingColumns, sort, asc, onSort }: Props) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-surface-border">
          {leadingColumns.map((lc, i) => (
            <th key={i} className="text-left px-4 py-3 text-gray-500 font-medium">{lc.label}</th>
          ))}
          {columns.map(c => (
            <th
              key={c.key}
              className="px-3 py-3 text-gray-500 font-medium cursor-pointer hover:text-white text-right"
              onClick={() => onSort(c.key)}
            >
              {c.label} {sort === c.key ? (asc ? '↑' : '↓') : ''}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map(row => (
          <tr key={rowKey(row)} className="border-b border-surface-border hover:bg-surface-hover">
            {leadingColumns.map((lc, i) => (
              <td key={i} className={clsx(i === 0 ? 'px-4 py-3' : 'px-3 py-3', i > 0 && 'text-gray-400')}>
                {lc.render(row)}
              </td>
            ))}
            {columns.map(c => (
              <td key={c.key} className="px-3 py-3 text-right text-gray-300">{formatCell(row, c)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
