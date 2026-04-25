import { useState } from 'react'
import { useApprovalList } from '../hooks/useApproval'
import type { ApprovalStatus } from '../types/approval'
import { STATUS_LABEL } from '../types/approval'
import { ApprovalCard } from '../components/approval/ApprovalCard'
import { PageSpinner } from '../components/ui/Spinner'
import { cn } from '../lib/utils'

const STATUS_FILTERS: Array<{ value: ApprovalStatus | 'all'; label: string }> = [
  { value: 'all', label: 'Tout' },
  { value: 'awaiting_approval', label: STATUS_LABEL['awaiting_approval'] },
  { value: 'approved', label: STATUS_LABEL['approved'] },
  { value: 'rejected', label: STATUS_LABEL['rejected'] },
  { value: 'executed', label: STATUS_LABEL['executed'] },
  { value: 'proposed', label: STATUS_LABEL['proposed'] },
]

const MODULE_FILTERS = ['all', 'MM', 'SD'] as const

const PAGE_SIZE = 20

export function ApprovalListPage() {
  const [statusFilter, setStatusFilter] = useState<ApprovalStatus | 'all'>('all')
  const [moduleFilter, setModuleFilter] = useState<'all' | 'MM' | 'SD'>('all')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useApprovalList()

  if (isLoading) return <PageSpinner />

  const allItems = data?.items ?? []

  const filtered = allItems.filter((r) => {
    if (statusFilter !== 'all' && r.status !== statusFilter) return false
    if (moduleFilter !== 'all' && r.context.module !== moduleFilter) return false
    return true
  })

  const sorted = [...filtered].sort((a, b) => new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime())
  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)
  const paginated = sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <div className="max-w-4xl space-y-4 animate-fade-in">
      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        {/* Status filter */}
        <div className="flex flex-wrap gap-1">
          {STATUS_FILTERS.map(({ value, label }) => {
            const count = value === 'all' ? allItems.length : allItems.filter((r) => r.status === value).length
            return (
              <button
                key={value}
                onClick={() => { setStatusFilter(value); setPage(1) }}
                className={cn(
                  'px-3 py-1 rounded-lg text-xs font-medium transition-colors',
                  statusFilter === value
                    ? 'bg-accent-blue text-white'
                    : 'bg-bg-card border border-border text-text-secondary hover:border-border-strong',
                )}
              >
                {label}
                {count > 0 && (
                  <span className="ml-1.5 opacity-70">{count}</span>
                )}
              </button>
            )
          })}
        </div>

        {/* Module filter */}
        <div className="flex gap-1">
          {MODULE_FILTERS.map((m) => (
            <button
              key={m}
              onClick={() => { setModuleFilter(m); setPage(1) }}
              className={cn(
                'px-3 py-1 rounded-lg text-xs font-medium transition-colors',
                moduleFilter === m
                  ? 'bg-white/15 text-text-primary'
                  : 'bg-bg-card border border-border text-text-secondary hover:border-border-strong',
              )}
            >
              {m === 'all' ? 'Tous modules' : m}
            </button>
          ))}
        </div>
      </div>

      {/* List */}
      {paginated.length === 0 ? (
        <div className="py-16 text-center text-sm text-text-muted">
          Aucune demande ne correspond aux filtres sélectionnés.
        </div>
      ) : (
        <>
          <div className="space-y-2">
            {paginated.map((a) => (
              <ApprovalCard key={a.request_id} approval={a} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-text-muted">
                {filtered.length} demande(s) — page {page}/{totalPages}
              </span>
              <div className="flex gap-1">
                {Array.from({ length: totalPages }, (_, i) => (
                  <button
                    key={i}
                    onClick={() => setPage(i + 1)}
                    className={cn(
                      'w-7 h-7 rounded-lg text-xs font-medium transition-colors',
                      page === i + 1
                        ? 'bg-accent-blue text-white'
                        : 'bg-bg-card border border-border text-text-secondary hover:border-border-strong',
                    )}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Auto-refresh indicator */}
      <div className="flex items-center gap-1.5 text-xs text-text-muted">
        <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
        Actualisation automatique toutes les 30 s
      </div>
    </div>
  )
}
