import type { DiagnosisResult } from '../../types/sap'
import { IssueCard } from './IssueCard'

interface DiagnosisPanelProps {
  diagnosis: DiagnosisResult
}

export function DiagnosisPanel({ diagnosis }: DiagnosisPanelProps) {
  return (
    <div className="space-y-4">
      <IssueCard diagnosis={diagnosis} />
      {diagnosis.affected_documents.length > 0 && (
        <div className="bg-bg-card border border-border rounded-xl p-4">
          <p className="text-xs font-medium text-text-muted mb-2">Documents affectés</p>
          <div className="flex flex-wrap gap-2">
            {diagnosis.affected_documents.map((doc) => (
              <code key={doc} className="text-xs bg-white/10 text-text-primary px-2 py-0.5 rounded">
                {doc}
              </code>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
