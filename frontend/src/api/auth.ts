import { apiClient } from './client'
import type { Token, CurrentUser, UserResponse, UserCreate } from '../types/auth'

export async function login(email: string, password: string): Promise<Token> {
  // OAuth2PasswordRequestForm requires application/x-www-form-urlencoded
  const params = new URLSearchParams()
  params.append('username', email)
  params.append('password', password)

  const { data } = await apiClient.post<Token>('/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export async function refresh(refreshToken: string): Promise<Token> {
  const { data } = await apiClient.post<Token>('/auth/refresh', {
    refresh_token: refreshToken,
  })
  return data
}

export async function me(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>('/auth/me')
  return data
}

export async function logout(): Promise<void> {
  await apiClient.post('/auth/logout').catch(() => {
    // Best-effort — clear client state regardless
  })
}

export async function createUser(payload: UserCreate): Promise<UserResponse> {
  const { data } = await apiClient.post<UserResponse>('/auth/users', payload)
  return data
}

export async function listUsers(activeOnly = true): Promise<UserResponse[]> {
  const { data } = await apiClient.get<UserResponse[]>('/auth/users', {
    params: { active_only: activeOnly },
  })
  return data
}

export async function deactivateUser(userId: string): Promise<void> {
  await apiClient.patch(`/auth/users/${userId}/deactivate`)
}

export function meFromToken(token: CurrentUser): CurrentUser {
  return token
}
