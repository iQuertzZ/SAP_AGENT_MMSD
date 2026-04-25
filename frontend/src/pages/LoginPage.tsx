import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuth } from '../hooks/useAuth'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'

const schema = z.object({
  email: z.string().email('Email invalide'),
  password: z.string().min(1, 'Mot de passe requis'),
})

type FormData = z.infer<typeof schema>

export function LoginPage() {
  const { isAuthenticated, loginMutation } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) navigate('/', { replace: true })
  }, [isAuthenticated, navigate])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  const onSubmit = (data: FormData) => {
    loginMutation.mutate({ email: data.email, password: data.password })
  }

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center p-4">
      <div className="w-full max-w-sm animate-fade-in">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <span className="text-accent-blue text-3xl">◈</span>
          <div>
            <p className="text-base font-semibold text-text-primary">SAP MM/SD</p>
            <p className="text-xs text-text-secondary -mt-0.5">AI Copilot</p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-bg-card border border-border rounded-2xl p-6 shadow-xl">
          <h1 className="text-lg font-semibold text-text-primary mb-1">Connexion</h1>
          <p className="text-sm text-text-secondary mb-6">
            Accédez au tableau de bord consultant
          </p>

          <form onSubmit={(e) => void handleSubmit(onSubmit)(e)} className="space-y-4">
            <Input
              label="Email"
              type="email"
              placeholder="consultant@example.com"
              autoComplete="email"
              error={errors.email?.message}
              {...register('email')}
            />
            <Input
              label="Mot de passe"
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
              error={errors.password?.message}
              {...register('password')}
            />
            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full mt-2"
              loading={loginMutation.isPending}
            >
              Se connecter
            </Button>
          </form>
        </div>

        <p className="text-center text-xs text-text-muted mt-4">
          Admin par défaut : admin@sap-copilot.local / changeme
        </p>
      </div>
    </div>
  )
}
