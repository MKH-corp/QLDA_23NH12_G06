export type UserRole = 'admin' | 'manager' | 'staff';

export interface AuthUser {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
  department_id: number;
  is_active: boolean;
  created_at: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
}
