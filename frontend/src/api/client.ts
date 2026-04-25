import axios from 'axios'
import type { InternalAxiosRequestConfig } from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
})

// Attach Bearer token from localStorage
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

// Handle 401: try refresh, then retry; on failure clear session
apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    // Don't attempt refresh on the login or refresh endpoints themselves
    const url: string = original.url ?? ''
    if (url.includes('/auth/login') || url.includes('/auth/refresh')) {
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshSubscribers.push((token) => {
          original.headers.Authorization = `Bearer ${token}`
          resolve(apiClient(original))
        })
        // Attach reject to avoid unhandled promise
        void reject
      })
    }

    original._retry = true
    isRefreshing = true

    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) throw new Error('No refresh token')

      const { data } = await axios.post<{ access_token: string; refresh_token: string }>(
        `${BASE_URL}/api/v1/auth/refresh`,
        { refresh_token: refreshToken },
      )

      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)

      onTokenRefreshed(data.access_token)
      original.headers.Authorization = `Bearer ${data.access_token}`
      return apiClient(original)
    } catch {
      // Refresh failed — clear session and redirect
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
      return Promise.reject(error)
    } finally {
      isRefreshing = false
    }
  },
)
