import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { analyze } from '../api/analyze'
import type { AnalyzeRequest, AnalysisResponse } from '../types/sap'

export function useAnalyze(onSuccess?: (data: AnalysisResponse) => void) {
  return useMutation({
    mutationFn: (payload: AnalyzeRequest) => analyze(payload),
    onSuccess: (data) => {
      toast.success(`Analyse terminée — ${data.recommended_actions.length} action(s) recommandée(s)`)
      onSuccess?.(data)
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof Error ? err.message : 'Erreur lors de l\'analyse'
      toast.error(msg)
    },
  })
}
