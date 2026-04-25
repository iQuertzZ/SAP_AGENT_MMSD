export type SAPModule = 'MM' | 'SD'

export type DocumentStatus =
  | 'OPEN'
  | 'BLOCKED'
  | 'PARKED'
  | 'POSTED'
  | 'REVERSED'
  | 'COMPLETED'
  | 'ERROR'
  | 'PENDING'

export type IssueSeverity = 'low' | 'medium' | 'high' | 'critical'

export type IssueType =
  | 'GRIR_MISMATCH'
  | 'MISSING_GR'
  | 'INVOICE_BLOCKED'
  | 'PRICE_VARIANCE'
  | 'QUANTITY_VARIANCE'
  | 'STOCK_INCONSISTENCY'
  | 'PO_NOT_RELEASED'
  | 'VENDOR_BLOCKED'
  | 'TOLERANCE_EXCEEDED'
  | 'CREDIT_BLOCK'
  | 'PRICING_ERROR'
  | 'DELIVERY_BLOCK'
  | 'BILLING_BLOCK'
  | 'MATERIAL_NOT_AVAILABLE'
  | 'PARTNER_MISSING'
  | 'INCOMPLETION_LOG'
  | 'OUTPUT_MISSING'
  | 'UNKNOWN'

export type RiskLevel = 'low' | 'medium' | 'high'

export interface SAPContext {
  tcode: string
  module: SAPModule
  document_id: string
  document_type: string | null
  status: DocumentStatus
  company_code: string | null
  plant: string | null
  sales_org: string | null
  user: string | null
  fiscal_year: string | null
  raw_data: Record<string, unknown>
}

export interface DiagnosisResult {
  issue_type: IssueType
  root_cause: string
  severity: IssueSeverity
  confidence: number
  details: Record<string, unknown>
  supporting_evidence: string[]
  affected_documents: string[]
  source: 'rule_engine' | 'ai' | 'hybrid'
}

export interface RecommendedAction {
  action_id: string
  tcode: string
  description: string
  risk: RiskLevel
  confidence: number
  parameters: Record<string, unknown>
  prerequisites: string[]
  rollback_plan: string
  estimated_duration_minutes: number
  requires_authorization: string[]
  documentation_url: string | null
}

export interface AnalyzeRequest {
  tcode: string
  module: SAPModule
  document_id: string
  document_type?: string
  status?: DocumentStatus
  company_code?: string
  plant?: string
  sales_org?: string
  user?: string
  fiscal_year?: string
}

export interface AnalysisResponse {
  request_id: string
  context: SAPContext
  diagnosis: DiagnosisResult
  recommended_actions: RecommendedAction[]
  primary_action: RecommendedAction | null
  analyzed_at: string
  processing_ms: number
}

export interface HealthResponse {
  status: string
  version: string
  ai_enabled: boolean
  connector: string
  execution_enabled: boolean
}

export const TCODE_OPTIONS = [
  'MIRO', 'MIGO', 'ME21N', 'ME23N', 'MR11', 'MR8M', 'MRM1',
  'VA01', 'VA02', 'VA03', 'VL01N', 'VF01', 'VF02', 'VF03', 'VKM1',
  'FB60', 'F-28', 'MRBR', 'MB1C',
] as const
