import type { SAPContext, DiagnosisResult, RecommendedAction } from './sap'
import type { SimulationResult } from './simulation'

export type ApprovalStatus =
  | 'proposed'
  | 'awaiting_approval'
  | 'approved'
  | 'rejected'
  | 'executed'
  | 'rolled_back'
  | 'expired'

export interface ExecutionResult {
  success: boolean
  sap_document_number: string | null
  message: string
  executed_at: string
  execution_log: string[]
}

export interface ApprovalRequest {
  request_id: string
  context: SAPContext
  diagnosis: DiagnosisResult
  recommended_action: RecommendedAction
  simulation: SimulationResult
  status: ApprovalStatus
  requested_by: string | null
  requested_at: string
  approver: string | null
  approval_timestamp: string | null
  rejection_reason: string | null
  execution_result: ExecutionResult | null
  expires_at: string | null
}

export interface ApprovalResponse {
  request_id: string
  status: ApprovalStatus
  message: string
}

export interface ApprovalListResponse {
  total: number
  items: ApprovalRequest[]
}

export interface ApprovePayload {
  request_id: string
  approver: string
  comment?: string
}

export interface RejectPayload {
  request_id: string
  approver: string
  reason: string
}

export interface ExecutePayload {
  request_id: string
  executor: string
}

export const STATUS_LABEL: Record<ApprovalStatus, string> = {
  proposed: 'Proposed',
  awaiting_approval: 'Awaiting Approval',
  approved: 'Approved',
  rejected: 'Rejected',
  executed: 'Executed',
  rolled_back: 'Rolled Back',
  expired: 'Expired',
}

export const WORKFLOW_STEPS: ApprovalStatus[] = [
  'proposed',
  'awaiting_approval',
  'approved',
  'executed',
]
