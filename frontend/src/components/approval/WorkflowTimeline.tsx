import { Check } from 'lucide-react'
import type { ApprovalRequest, ApprovalStatus } from '../../types/approval'
import { WORKFLOW_STEPS, STATUS_LABEL } from '../../types/approval'
import { cn } from '../../lib/utils'
import { formatDate } from '../../lib/utils'

interface WorkflowTimelineProps {
  approval: ApprovalRequest
}

function getStepDate(approval: ApprovalRequest, step: ApprovalStatus): string | null {
  switch (step) {
    case 'proposed': return approval.requested_at
    case 'awaiting_approval': return approval.requested_at
    case 'approved': return approval.approval_timestamp
    case 'executed': return approval.execution_result?.executed_at ?? null
    default: return null
  }
}

function stepState(
  step: ApprovalStatus,
  current: ApprovalStatus,
): 'done' | 'active' | 'future' {
  const steps = WORKFLOW_STEPS
  const stepIdx = steps.indexOf(step)
  const currentIdx = steps.indexOf(current)

  if (current === 'rejected') {
    if (stepIdx <= 1) return 'done'
    return 'future'
  }
  if (currentIdx < 0) return 'future'
  if (stepIdx < currentIdx) return 'done'
  if (stepIdx === currentIdx) return 'active'
  return 'future'
}

export function WorkflowTimeline({ approval }: WorkflowTimelineProps) {
  const isRejected = approval.status === 'rejected'

  return (
    <div className="flex items-start gap-0">
      {WORKFLOW_STEPS.map((step, i) => {
        const state = stepState(step, approval.status)
        const date = getStepDate(approval, step)
        const isLast = i === WORKFLOW_STEPS.length - 1

        return (
          <div key={step} className="flex-1 flex flex-col items-center">
            <div className="flex items-center w-full">
              {/* Circle */}
              <div
                className={cn(
                  'w-7 h-7 rounded-full flex items-center justify-center shrink-0 border-2 z-10',
                  state === 'done'
                    ? 'bg-success border-success text-white'
                    : state === 'active'
                      ? 'bg-accent-blue border-accent-blue text-white'
                      : 'bg-transparent border-border text-text-muted',
                )}
              >
                {state === 'done' ? (
                  <Check className="w-3.5 h-3.5" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-current" />
                )}
              </div>
              {/* Connector */}
              {!isLast && (
                <div
                  className={cn(
                    'flex-1 h-0.5',
                    state === 'done' ? 'bg-success' : 'bg-border',
                  )}
                />
              )}
            </div>
            {/* Label */}
            <div className="mt-2 text-center px-1">
              <p
                className={cn(
                  'text-xs font-medium',
                  state === 'active'
                    ? 'text-accent-blue'
                    : state === 'done'
                      ? 'text-text-secondary'
                      : 'text-text-muted',
                )}
              >
                {STATUS_LABEL[step]}
              </p>
              {date && (
                <p className="text-[10px] text-text-muted mt-0.5">{formatDate(date)}</p>
              )}
            </div>
          </div>
        )
      })}

      {/* Rejected indicator */}
      {isRejected && (
        <div className="ml-4 flex flex-col items-center">
          <div className="w-7 h-7 rounded-full flex items-center justify-center border-2 border-danger bg-danger/20 text-red-400 text-xs font-bold">
            ✕
          </div>
          <div className="mt-2 text-center">
            <p className="text-xs font-medium text-red-400">Rejeté</p>
            {approval.approval_timestamp && (
              <p className="text-[10px] text-text-muted mt-0.5">
                {formatDate(approval.approval_timestamp)}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
