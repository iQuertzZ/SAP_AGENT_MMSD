import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { login as apiLogin, me, logout as apiLogout } from '../api/auth'
import { useAuthStore } from '../store/auth.store'
import type { SAPRole } from '../types/auth'
import { hasMinRole } from '../types/auth'

export function useAuth() {
  const { user, accessToken, setAuth, logout: storeLogout } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const isAuthenticated = !!accessToken && !!user

  function can(minRole: SAPRole): boolean {
    if (!user) return false
    return hasMinRole(user.role, minRole)
  }

  const loginMutation = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      apiLogin(email, password),
    onSuccess: async (token) => {
      localStorage.setItem('access_token', token.access_token)
      localStorage.setItem('refresh_token', token.refresh_token)
      const userInfo = await me()
      setAuth(userInfo, token.access_token, token.refresh_token)
      navigate('/')
    },
    onError: () => {
      toast.error('Email ou mot de passe incorrect')
    },
  })

  const logoutFn = useCallback(async () => {
    await apiLogout().catch(() => undefined)
    storeLogout()
    queryClient.clear()
    navigate('/login')
  }, [storeLogout, navigate, queryClient])

  return { user, isAuthenticated, can, loginMutation, logout: logoutFn }
}

export function useMe() {
  const { accessToken } = useAuthStore()
  return useQuery({
    queryKey: ['me'],
    queryFn: me,
    enabled: !!accessToken,
    staleTime: 5 * 60 * 1000,
  })
}
