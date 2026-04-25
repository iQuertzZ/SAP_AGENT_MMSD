import { apiClient } from './client'
import type { AnalyzeRequest, AnalysisResponse, HealthResponse } from '../types/sap'
import type { SimulateRequest, SimulationResponse } from '../types/simulation'

export async function analyze(payload: AnalyzeRequest): Promise<AnalysisResponse> {
  const { data } = await apiClient.post<AnalysisResponse>('/analyze', payload)
  return data
}

export async function simulate(payload: SimulateRequest): Promise<SimulationResponse> {
  const { data } = await apiClient.post<SimulationResponse>('/simulate', payload)
  return data
}

export async function health(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/health')
  return data
}
