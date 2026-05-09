import { apiRequest } from './client';

export interface KpiSnapshot {
  total_score: number; 
  tasks_completed: number; 
  tasks_overdue: number;
  breakdown: { 
    base_score: number; 
    on_time_bonus: number; 
    overdue_penalty_amount: number; 
    reopen_penalty_amount: number; 
  };
  updated_at: string;
}

export const getMyKpi = () => apiRequest<KpiSnapshot>('/kpi/me');
export const getTeamRanking = () => apiRequest<any[]>('/kpi/team');

// THÊM DÒNG NÀY:
export const getUserKpi = (userId: number) => apiRequest<KpiSnapshot>(`/kpi/${userId}`);