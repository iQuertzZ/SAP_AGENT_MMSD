import { apiClient } from './client'
import type { AnalyzeRequest } from '../types/sap'
import type {
  ApprovalRequest,
  ApprovalResponse,
  ApprovalListResponse,
  ApprovePayload,
  RejectPayload,
  ExecutePayload,
} from '../types/approval'

export async function submitApproval(payload: AnalyzeRequest): Promise<ApprovalRequest> {
  const { data } = await apiClient.post<ApprovalRequest>('/approval/submit', payload)
  return data
}

export async function getApproval(requestId: string): Promise<ApprovalRequest> {
  const { data } = await apiClient.get<ApprovalRequest>(`/approval/${requestId}`)
  return data
}

export async function listApprovals(pendingOnly = false): Promise<ApprovalListResponse> {
  const { data } = await apiClient.get<ApprovalListResponse>('/approval/', {
    params: { pending_only: pendingOnly },
  })
  return data
}

export async function approveRequest(
  requestId: string,
  payload: Omit<ApprovePayload, 'request_id'>,
): Promise<ApprovalResponse> {
  const { data } = await apiClient.post<ApprovalResponse>(`/approval/${requestId}/approve`, {
    request_id: requestId,
    ...payload,
  })
  return data
}

export async function rejectRequest(
  requestId: string,
  payload: Omit<RejectPayload, 'request_id'>,
): Promise<ApprovalResponse> {
  const { data } = await apiClient.post<ApprovalResponse>(`/approval/${requestId}/reject`, {
    request_id: requestId,
    ...payload,
  })
  return data
}

export async function executeApproval(payload: ExecutePayload): Promise<ApprovalRequest> {
  const { data } = await apiClient.post<ApprovalRequest>('/execute', payload)
  return data
}

export async function getAuditLog(): Promise<Record<string, unknown>[]> {
  const { data } = await apiClient.get<Record<string, unknown>[]>('/execute/audit')
  return data
}
