import { apiRequest } from './client';

// --- TYPES ---
export interface Project { id: number; name: string; status: string; progress: number; total_tasks: number; }
export interface Notification { id: number; title: string; message: string; type: string; is_read: boolean; created_at: string; }
export interface KpiRecord { user_id: number; name: string; current_month_kpi: number; tasks_done: number; }

// --- PROJECTS API ---
export const getProjects = () => apiRequest<Project[]>('/projects/');
export const createProject = (data: Partial<Project>) => apiRequest<Project>('/projects/', { method: 'POST', body: JSON.stringify(data) });
export const deleteProject = (id: number) => apiRequest(`/projects/${id}`, { method: 'DELETE' });

// --- KPI API ---
export const getKpiAnalytics = () => apiRequest<KpiRecord[]>('/kpi/analytics');

// --- NOTIFICATIONS API ---
export const getNotifications = () => apiRequest<Notification[]>('/notifications/');
export const markNotificationAsRead = (id: number) => apiRequest(`/notifications/${id}/read`, { method: 'PUT' });

// Thêm vào api/services.ts
export interface User { id: number; full_name: string; email: string; role: string; is_active: boolean; department_id: number; }
export interface ProductivityReport { department_name: string; total_tasks: number; completed: number; overdue: number; productivity_score: number; }

export const getUsers = (search: string = '') => apiRequest<User[]>(`/users/?skip=0&limit=100&search=${search}`);
export const getProductivityReport = () => apiRequest<ProductivityReport[]>('/reports/productivity');