import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Search, ChevronRight } from 'lucide-react'
import { useAnalyze } from '../hooks/useAnalyze'
import { useSubmitApproval } from '../hooks/useApproval'
import type { AnalysisResponse, RecommendedAction } from '../types/sap'
import { TCODE_OPTIONS } from '../types/sap'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Card, CardTitle } from '../components/ui/Card'
import { DiagnosisPanel } from '../components/diagnosis/DiagnosisPanel'
import { ActionGrid } from '../components/actions/ActionGrid'
import { SimulationPanel } from '../components/simulation/SimulationPanel'
import { SkeletonCard } from '../components/ui/Spinner'

const schema = z.object({
  tcode: z.string().min(1, 'TCode requis'),
  module: z.enum(['MM', 'SD']),
  document_id: z.string().min(1, 'Numéro de document requis'),
  status: z.enum(['OPEN', 'BLOCKED', 'PARKED', 'POSTED', 'REVERSED', 'COMPLETED', 'ERROR', 'PENDING']),
  company_code: z.string().optional(),
  plant: z.string().optional(),
})

type FormData = z.infer<typeof schema>

type Step = 'form' | 'results' | 'submitted'

export function AnalyzePage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('form')
  const [result, setResult] = useState<AnalysisResponse | null>(null)
  const [selectedAction, setSelectedAction] = useState<RecommendedAction | null>(null)
  const [submittedId, setSubmittedId] = useState<string | null>(null)

  const analyzeMut = useAnalyze((data) => {
    setResult(data)
    setSelectedAction(data.primary_action ?? data.recommended_actions[0] ?? null)
    setStep('results')
  })

  const submitMut = useSubmitApproval()

  const { register, handleSubmit, control, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { status: 'BLOCKED', module: 'MM' },
  })

  const onAnalyze = (data: FormData) => {
    analyzeMut.mutate(data)
  }

  const onSubmitApproval = () => {
    if (!result) return
    const ctx = result.context
    const analyzePayload = {
      tcode: ctx.tcode,
      module: ctx.module,
      document_id: ctx.document_id,
      status: ctx.status,
      document_type: ctx.document_type ?? undefined,
      company_code: ctx.company_code ?? undefined,
      plant: ctx.plant ?? undefined,
      sales_org: ctx.sales_org ?? undefined,
      user: ctx.user ?? undefined,
      fiscal_year: ctx.fiscal_year ?? undefined,
    }
    submitMut.mutate(analyzePayload, {
      onSuccess: (approval) => {
        setSubmittedId(approval.request_id)
        setStep('submitted')
      },
    })
  }

  return (
    <div className="max-w-5xl space-y-6 animate-fade-in">
      {/* Stepper */}
      <div className="flex items-center gap-2 text-sm">
        {['Contexte', 'Diagnostic', 'Actions', 'Soumission'].map((label, i) => {
          const stepIdx = ['form', 'results', 'results', 'submitted'].indexOf(step)
          const active = i <= stepIdx
          return (
            <div key={label} className="flex items-center gap-2">
              <span
                className={`w-5 h-5 rounded-full text-xs flex items-center justify-center font-semibold ${
                  active ? 'bg-accent-blue text-white' : 'bg-white/10 text-text-muted'
                }`}
              >
                {i + 1}
              </span>
              <span className={active ? 'text-text-primary' : 'text-text-muted'}>{label}</span>
              {i < 3 && <ChevronRight className="w-3 h-3 text-text-muted" />}
            </div>
          )
        })}
      </div>

      {/* Step 1 — Form */}
      {step === 'form' && (
        <Card>
          <CardTitle className="text-base mb-4">Contexte SAP</CardTitle>
          <form onSubmit={(e) => void handleSubmit(onAnalyze)(e)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {/* TCode */}
              <Controller
                name="tcode"
                control={control}
                render={({ field }) => (
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-text-secondary">TCode</label>
                    <input
                      list="tcode-list"
                      className="h-9 px-3 rounded-lg bg-bg-secondary border border-border text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue/50 focus:border-accent-blue/50"
                      placeholder="MIRO"
                      {...field}
                    />
                    <datalist id="tcode-list">
                      {TCODE_OPTIONS.map((t) => <option key={t} value={t} />)}
                    </datalist>
                    {errors.tcode && <p className="text-xs text-red-400">{errors.tcode.message}</p>}
                  </div>
                )}
              />

              <Input
                label="Numéro de document"
                placeholder="51000321"
                error={errors.document_id?.message}
                {...register('document_id')}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <Controller
                name="module"
                control={control}
                render={({ field }) => (
                  <Select
                    label="Module"
                    options={[{ value: 'MM', label: 'MM — Materials Management' }, { value: 'SD', label: 'SD — Sales & Distribution' }]}
                    {...field}
                  />
                )}
              />
              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <Select
                    label="Statut"
                    options={[
                      { value: 'OPEN', label: 'OPEN' },
                      { value: 'BLOCKED', label: 'BLOCKED' },
                      { value: 'PARKED', label: 'PARKED' },
                      { value: 'POSTED', label: 'POSTED' },
                      { value: 'ERROR', label: 'ERROR' },
                      { value: 'PENDING', label: 'PENDING' },
                    ]}
                    {...field}
                  />
                )}
              />
              <Input label="Code société (optionnel)" placeholder="1000" {...register('company_code')} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Input label="Usine (optionnel)" placeholder="1000" {...register('plant')} />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={analyzeMut.isPending}
              className="w-full"
            >
              <Search className="w-4 h-4" />
              Analyser avec l'IA
            </Button>
          </form>
        </Card>
      )}

      {/* Loading skeleton */}
      {analyzeMut.isPending && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {/* Step 2+3 — Results */}
      {step === 'results' && result && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-3">Diagnostic</h3>
              <DiagnosisPanel diagnosis={result.diagnosis} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-3">
                Actions recommandées ({result.recommended_actions.length})
              </h3>
              <ActionGrid
                actions={result.recommended_actions}
                selectedId={selectedAction?.action_id ?? null}
                onSelect={setSelectedAction}
              />
            </div>
          </div>

          <div className="space-y-4">
            {selectedAction && (
              <>
                <h3 className="text-sm font-semibold text-text-primary">Simulation d'impact</h3>
                <SimulationPanel
                  simulation={result.context.raw_data?.simulation as never ?? {
                    documents_affected: 1,
                    financial: { posting_required: false, amount: null, currency: null, gl_accounts_affected: [], cost_centers_affected: [] },
                    workflow: { steps_triggered: [], approvals_required: [], notifications_sent: [] },
                    risk_score: selectedAction.risk === 'high' ? 0.8 : selectedAction.risk === 'medium' ? 0.5 : 0.2,
                    warnings: [],
                    blockers: [],
                    reversible: true,
                    simulation_notes: '',
                  }}
                  onSubmit={onSubmitApproval}
                  isSubmitting={submitMut.isPending}
                />
              </>
            )}
          </div>
        </div>
      )}

      {/* Step 4 — Submitted */}
      {step === 'submitted' && submittedId && (
        <Card className="text-center py-8">
          <div className="text-5xl mb-4">✓</div>
          <h3 className="text-lg font-semibold text-text-primary mb-2">Demande soumise</h3>
          <p className="text-sm text-text-secondary mb-6">
            La demande d'approbation <code className="font-mono text-accent-blue">{submittedId.slice(0, 8)}</code> a été créée.
          </p>
          <div className="flex justify-center gap-3">
            <Button variant="primary" onClick={() => navigate(`/approval/${submittedId}`)}>
              Voir la demande
            </Button>
            <Button variant="secondary" onClick={() => { setStep('form'); setResult(null) }}>
              Nouvelle analyse
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}
