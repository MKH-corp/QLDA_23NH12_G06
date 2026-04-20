import type { DepartmentOption, UserOption } from '../types/reference';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Request failed');
  }

  return response.json() as Promise<T>;
}

export async function getDepartments(): Promise<DepartmentOption[]> {
  return request<DepartmentOption[]>('/references/departments');
}

export async function getUsers(): Promise<UserOption[]> {
  return request<UserOption[]>('/references/users');
}
