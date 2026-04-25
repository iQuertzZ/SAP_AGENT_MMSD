import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { simulate } from '../api/analyze'
import type { SimulateRequest, SimulationResponse } from '../types/simulation'

export function useSimulation(onSuccess?: (data: SimulationResponse) => void) {
  return useMutation({
    mutationFn: (payload: SimulateRequest) => simulate(payload),
    onSuccess: (data) => {
      toast.success('Simulation terminée')
      onSuccess?.(data)
    },
    onError: () => {
      toast.error('Erreur lors de la simulation')
    },
  })
}
