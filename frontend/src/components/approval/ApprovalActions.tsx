import { useState } from 'react'
import { CheckCircle, XCircle, PlayCircle } from 'lucide-react'
import type { ApprovalRequest } from '../../types/approval'
import { Button } from '../ui/Button'
import { Modal } from '../ui/Modal'
import { Input } from '../ui/Input'
import { useApprove, useReject, useExecute } from '../../hooks/useApproval'
import { useAuthStore } from '../../store/auth.store'
import { hasMinRole } from '../../types/auth'

interface ApprovalActionsProps {
  approval: ApprovalRequest
}

export function ApprovalActions({ approval }: ApprovalActionsProps) {
  const { user } = useAuthStore()
  const [approveOpen, setApproveOpen] = useState(false)
  const [rejectOpen, setRejectOpen] = useState(false)
  const [executeOpen, setExecuteOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [approveComment, setApproveComment] = useState('')

  const approveMut = useApprove()
  const rejectMut = useReject()
  const executeMut = useExecute()

  if (!user) return null

  const isManager = hasMinRole(user.role, 'manager')
  const isAdmin = user.role === 'admin'
  const canApprove = isManager && approval.status === 'awaiting_approval'
  const canExecute = isAdmin && approval.status === 'approved'

  if (!canApprove && !canExecute) return null

  const handleApprove = () => {
    approveMut.mutate(
      {
        requestId: approval.request_id,
        payload: { approver: user.email, comment: approveComment || undefined },
      },
      { onSuccess: () => setApproveOpen(false) },
    )
  }

  const handleReject = () => {
    if (!rejectReason.trim()) return
    rejectMut.mutate(
      {
        requestId: approval.request_id,
        payload: { approver: user.email, reason: rejectReason },
      },
      { onSuccess: () => setRejectOpen(false) },
    )
  }

  const handleExecute = () => {
    executeMut.mutate(
      { request_id: approval.request_id, executor: user.email },
      { onSuccess: () => setExecuteOpen(false) },
    )
  }

  return (
    <>
      <div className="flex gap-2 flex-wrap">
        {canApprove && (
          <>
            <Button variant="success" onClick={() => setApproveOpen(true)}>
              <CheckCircle className="w-4 h-4" />
              Approuver
            </Button>
            <Button variant="danger" onClick={() => setRejectOpen(true)}>
              <XCircle className="w-4 h-4" />
              Rejeter
            </Button>
          </>
        )}
        {canExecute && (
          <Button variant="primary" onClick={() => setExecuteOpen(true)}>
            <PlayCircle className="w-4 h-4" />
            Exécuter dans SAP
          </Button>
        )}
      </div>

      {/* Approve Modal */}
      <Modal
        open={approveOpen}
        onClose={() => setApproveOpen(false)}
        title="Confirmer l'approbation"
        footer={
          <>
            <Button variant="ghost" onClick={() => setApproveOpen(false)}>Annuler</Button>
            <Button variant="success" loading={approveMut.isPending} onClick={handleApprove}>
              Confirmer l'approbation
            </Button>
          </>
        }
      >
        <p className="text-sm text-text-secondary mb-3">
          Vous allez approuver la demande <code className="font-mono text-text-primary">{approval.request_id.slice(0, 8)}</code> —
          action <code className="font-mono text-accent-blue">{approval.recommended_action.tcode}</code> sur le document{' '}
          <strong>{approval.context.document_id}</strong>.
        </p>
        <Input
          label="Commentaire (optionnel)"
          value={approveComment}
          onChange={(e) => setApproveComment(e.target.value)}
          placeholder="Note pour le demandeur…"
        />
      </Modal>

      {/* Reject Modal */}
      <Modal
        open={rejectOpen}
        onClose={() => setRejectOpen(false)}
        title="Rejeter la demande"
        footer={
          <>
            <Button variant="ghost" onClick={() => setRejectOpen(false)}>Annuler</Button>
            <Button
              variant="danger"
              loading={rejectMut.isPending}
              onClick={handleReject}
              disabled={!rejectReason.trim()}
            >
              Confirmer le rejet
            </Button>
          </>
        }
      >
        <Input
          label="Raison du rejet *"
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="Expliquez pourquoi cette action ne peut pas être approuvée…"
        />
      </Modal>

      {/* Execute Modal */}
      <Modal
        open={executeOpen}
        onClose={() => setExecuteOpen(false)}
        title="Exécuter dans SAP"
        footer={
          <>
            <Button variant="ghost" onClick={() => setExecuteOpen(false)}>Annuler</Button>
            <Button variant="danger" loading={executeMut.isPending} onClick={handleExecute}>
              Exécuter maintenant
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-sm text-text-secondary">
            Cette action va exécuter{' '}
            <code className="font-mono text-accent-blue">{approval.recommended_action.tcode}</code> directement dans SAP.
            Cette opération <strong className="text-text-primary">ne peut pas être annulée automatiquement</strong>.
          </p>
          <div className="bg-warning/10 border border-warning/30 rounded-lg p-3 text-xs text-orange-300">
            Plan de rollback disponible : {approval.recommended_action.rollback_plan}
          </div>
        </div>
      </Modal>
    </>
  )
}
