export interface FinancialImpact {
  posting_required: boolean
  amount: number | null
  currency: string | null
  gl_accounts_affected: string[]
  cost_centers_affected: string[]
}

export interface WorkflowImpact {
  steps_triggered: string[]
  approvals_required: string[]
  notifications_sent: string[]
}

export interface SimulationResult {
  documents_affected: number
  financial: FinancialImpact
  workflow: WorkflowImpact
  risk_score: number
  warnings: string[]
  blockers: string[]
  reversible: boolean
  simulation_notes: string
}

export interface SimulationResponse {
  action_tcode: string
  simulation: SimulationResult
  simulated_at: string
}

export interface SimulateRequest {
  tcode: string
  module: string
  document_id: string
  status?: string
  action_tcode: string
  parameters?: Record<string, unknown>
}
