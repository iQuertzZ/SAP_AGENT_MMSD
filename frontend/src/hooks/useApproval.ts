import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  submitApproval,
  listApprovals,
  getApproval,
  approveRequest,
  rejectRequest,
  executeApproval,
  getAuditLog,
} from '../api/approval'
import type { AnalyzeRequest } from '../types/sap'
import type { ApprovePayload, RejectPayload, ExecutePayload } from '../types/approval'

export const approvalKeys = {
  all: ['approvals'] as const,
  list: (pendingOnly?: boolean) => ['approvals', 'list', pendingOnly] as const,
  detail: (id: string) => ['approvals', id] as const,
  audit: () => ['approvals', 'audit'] as const,
}

export function useApprovalList(pendingOnly = false) {
  return useQuery({
    queryKey: approvalKeys.list(pendingOnly),
    queryFn: () => listApprovals(pendingOnly),
    refetchInterval: 30_000,
  })
}

export function useApprovalDetail(requestId: string) {
  return useQuery({
    queryKey: approvalKeys.detail(requestId),
    queryFn: () => getApproval(requestId),
    enabled: !!requestId,
  })
}

export function useSubmitApproval() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: AnalyzeRequest) => submitApproval(payload),
    onSuccess: () => {
      toast.success('Demande soumise pour approbation')
      void qc.invalidateQueries({ queryKey: approvalKeys.all })
    },
    onError: (err: unknown) => {
      const detail =
        err instanceof Error ? err.message : 'Erreur lors de la soumission'
      toast.error(detail)
    },
  })
}

export function useApprove() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ requestId, payload }: { requestId: string; payload: Omit<ApprovePayload, 'request_id'> }) =>
      approveRequest(requestId, payload),
    onSuccess: (_data, { requestId }) => {
      toast.success('Demande approuvée')
      void qc.invalidateQueries({ queryKey: approvalKeys.detail(requestId) })
      void qc.invalidateQueries({ queryKey: approvalKeys.all })
    },
    onError: () => toast.error('Erreur lors de l\'approbation'),
  })
}

export function useReject() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ requestId, payload }: { requestId: string; payload: Omit<RejectPayload, 'request_id'> }) =>
      rejectRequest(requestId, payload),
    onSuccess: (_data, { requestId }) => {
      toast.success('Demande rejetée')
      void qc.invalidateQueries({ queryKey: approvalKeys.detail(requestId) })
      void qc.invalidateQueries({ queryKey: approvalKeys.all })
    },
    onError: () => toast.error('Erreur lors du rejet'),
  })
}

export function useExecute() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: ExecutePayload) => executeApproval(payload),
    onSuccess: (_data, payload) => {
      toast.success('Action exécutée dans SAP')
      void qc.invalidateQueries({ queryKey: approvalKeys.detail(payload.request_id) })
      void qc.invalidateQueries({ queryKey: approvalKeys.all })
    },
    onError: () => toast.error('Erreur lors de l\'exécution'),
  })
}

export function useAuditLog() {
  return useQuery({
    queryKey: approvalKeys.audit(),
    queryFn: getAuditLog,
  })
}
