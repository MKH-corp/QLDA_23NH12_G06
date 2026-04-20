import { apiRequest } from './client';
import type { DepartmentOption, UserOption } from '../types/reference';

export function getDepartments(): Promise<DepartmentOption[]> {
  return apiRequest<DepartmentOption[]>('/departments');
}

export function getUsers(): Promise<UserOption[]> {
  return apiRequest<UserOption[]>('/users');
}
