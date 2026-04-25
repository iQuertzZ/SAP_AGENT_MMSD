import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserResponse } from '../types/auth'

interface AuthState {
  user: UserResponse | null
  accessToken: string | null
  refreshToken: string | null
  setAuth: (user: UserResponse, accessToken: string, refreshToken: string) => void
  updateTokens: (accessToken: string, refreshToken: string) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,

      setAuth: (user, accessToken, refreshToken) => {
        // Keep localStorage in sync for the Axios interceptor
        localStorage.setItem('access_token', accessToken)
        localStorage.setItem('refresh_token', refreshToken)
        set({ user, accessToken, refreshToken })
      },

      updateTokens: (accessToken, refreshToken) => {
        localStorage.setItem('access_token', accessToken)
        localStorage.setItem('refresh_token', refreshToken)
        set({ accessToken, refreshToken })
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, accessToken: null, refreshToken: null })
      },
    }),
    {
      name: 'sap-copilot-auth',
      // Only persist user info — tokens are in localStorage for Axios interceptor
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    },
  ),
)
