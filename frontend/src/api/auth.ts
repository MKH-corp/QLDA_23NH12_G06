import { apiRequest } from './client';
import type { AuthUser, LoginPayload, LoginResponse } from '../types/auth';

export function login(payload: LoginPayload): Promise<LoginResponse> {
  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getMe(): Promise<AuthUser> {
  return apiRequest<AuthUser>('/auth/me');
}
