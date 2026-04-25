export type SAPRole = 'admin' | 'manager' | 'consultant' | 'service'

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface CurrentUser {
  user_id: string
  email: string
  role: SAPRole
  is_active: boolean
}

export interface UserResponse {
  user_id: string
  email: string
  full_name: string
  role: SAPRole
  is_active: boolean
  last_login: string | null
}

export interface UserCreate {
  email: string
  password: string
  full_name: string
  role: SAPRole
}

export const ROLE_LEVEL: Record<SAPRole, number> = {
  service: 1,
  consultant: 2,
  manager: 3,
  admin: 4,
}

export function hasMinRole(userRole: SAPRole, minRole: SAPRole): boolean {
  return ROLE_LEVEL[userRole] >= ROLE_LEVEL[minRole]
}
