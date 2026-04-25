import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { listUsers, createUser, deactivateUser } from '../api/auth'
import { health } from '../api/analyze'
import { useAuditLog } from '../hooks/useApproval'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Card, CardTitle } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { PageSpinner } from '../components/ui/Spinner'
import { formatDate } from '../lib/utils'
import type { SAPRole } from '../types/auth'
import { cn } from '../lib/utils'

type Tab = 'users' | 'health' | 'audit'

const createUserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8, 'Minimum 8 caractères'),
  full_name: z.string().min(1),
  role: z.enum(['admin', 'manager', 'consultant', 'service']),
})

type CreateUserData = z.infer<typeof createUserSchema>

export function AdminPage() {
  const [tab, setTab] = useState<Tab>('users')

  return (
    <div className="max-w-4xl space-y-4 animate-fade-in">
      {/* Tabs */}
      <div className="flex gap-1 bg-bg-secondary border border-border rounded-xl p-1 w-fit">
        {(['users', 'health', 'audit'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              'px-4 py-1.5 rounded-lg text-sm font-medium transition-colors capitalize',
              tab === t
                ? 'bg-accent-blue text-white'
                : 'text-text-secondary hover:text-text-primary',
            )}
          >
            {t === 'health' ? 'Santé système' : t === 'audit' ? 'Audit' : 'Utilisateurs'}
          </button>
        ))}
      </div>

      {tab === 'users' && <UsersTab />}
      {tab === 'health' && <HealthTab />}
      {tab === 'audit' && <AuditTab />}
    </div>
  )
}

function UsersTab() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => listUsers(false),
  })

  const createMut = useMutation({
    mutationFn: (d: CreateUserData) => createUser({ ...d, role: d.role as SAPRole }),
    onSuccess: () => {
      toast.success('Utilisateur créé')
      void qc.invalidateQueries({ queryKey: ['users'] })
      setShowCreate(false)
    },
    onError: () => toast.error('Erreur lors de la création'),
  })

  const deactivateMut = useMutation({
    mutationFn: (id: string) => deactivateUser(id),
    onSuccess: () => {
      toast.success('Utilisateur désactivé')
      void qc.invalidateQueries({ queryKey: ['users'] })
    },
  })

  const { register, handleSubmit, control, formState: { errors } } = useForm<CreateUserData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: { role: 'consultant' },
  })

  if (isLoading) return <PageSpinner />

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <CardTitle className="text-base">{users?.length ?? 0} utilisateur(s)</CardTitle>
        <Button variant="primary" size="sm" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? 'Annuler' : '+ Créer'}
        </Button>
      </div>

      {showCreate && (
        <Card className="bg-bg-secondary">
          <CardTitle className="mb-4">Nouvel utilisateur</CardTitle>
          <form onSubmit={(e) => void handleSubmit((d) => createMut.mutate(d))(e)} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <Input label="Email" type="email" error={errors.email?.message} {...register('email')} />
              <Input label="Nom complet" error={errors.full_name?.message} {...register('full_name')} />
              <Input label="Mot de passe" type="password" error={errors.password?.message} {...register('password')} />
              <Controller
                name="role"
                control={control}
                render={({ field }) => (
                  <Select
                    label="Rôle"
                    options={[
                      { value: 'consultant', label: 'Consultant' },
                      { value: 'manager', label: 'Manager' },
                      { value: 'admin', label: 'Admin' },
                      { value: 'service', label: 'Service' },
                    ]}
                    {...field}
                  />
                )}
              />
            </div>
            <Button type="submit" variant="primary" size="sm" loading={createMut.isPending}>
              Créer l'utilisateur
            </Button>
          </form>
        </Card>
      )}

      <div className="space-y-2">
        {users?.map((u) => (
          <Card key={u.user_id} className="flex items-center justify-between gap-4 p-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-8 h-8 rounded-full bg-accent-blue/20 flex items-center justify-center text-xs font-semibold text-accent-blue shrink-0">
                {u.email.charAt(0).toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="text-sm text-text-primary truncate">{u.email}</p>
                <p className="text-xs text-text-muted">{u.full_name} · {u.last_login ? formatDate(u.last_login) : 'Jamais connecté'}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Badge variant={u.is_active ? 'success' : 'muted'}>{u.is_active ? 'Actif' : 'Inactif'}</Badge>
              <Badge variant="muted" className="capitalize">{u.role}</Badge>
              {u.is_active && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-danger hover:text-red-300"
                  loading={deactivateMut.isPending}
                  onClick={() => deactivateMut.mutate(u.user_id)}
                >
                  Désactiver
                </Button>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}

function HealthTab() {
  const { data, isLoading } = useQuery({ queryKey: ['health'], queryFn: health })

  if (isLoading) return <PageSpinner />
  if (!data) return null

  const rows = [
    { label: 'Statut', value: data.status, ok: data.status === 'ok' },
    { label: 'Version', value: data.version },
    { label: 'Connecteur SAP', value: data.connector },
    { label: 'AI activée', value: data.ai_enabled ? 'Oui' : 'Non', ok: data.ai_enabled },
    { label: 'Exécution activée', value: data.execution_enabled ? 'Oui' : 'Non' },
  ]

  return (
    <Card>
      <CardTitle className="mb-4">État du système</CardTitle>
      <div className="space-y-3">
        {rows.map(({ label, value, ok }) => (
          <div key={label} className="flex items-center justify-between py-2 border-b border-border last:border-0">
            <span className="text-sm text-text-muted">{label}</span>
            <div className="flex items-center gap-2">
              {ok !== undefined && (
                <span className={`w-2 h-2 rounded-full ${ok ? 'bg-green-400' : 'bg-text-muted'}`} />
              )}
              <span className="text-sm font-medium text-text-primary">{String(value)}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

function AuditTab() {
  const { data, isLoading } = useAuditLog()

  if (isLoading) return <PageSpinner />

  if (!data || data.length === 0) {
    return (
      <div className="py-12 text-center text-sm text-text-muted">
        Aucune exécution enregistrée dans l'audit log.
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {data.map((entry, i) => (
        <Card key={i}>
          <pre className="text-xs font-mono text-text-secondary overflow-auto whitespace-pre-wrap">
            {JSON.stringify(entry, null, 2)}
          </pre>
        </Card>
      ))}
    </div>
  )
}
