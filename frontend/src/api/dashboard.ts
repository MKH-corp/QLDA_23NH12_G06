import { apiRequest } from './client';

export interface DashboardData {
  stats: {
    total_employees: number;
    active_departments: number;
    completed_tasks: number;
    avg_kpi: number;
  };
  department_charts: { id: number; name: string; score: number }[];
  top_performers: {
    id: number;
    full_name: string;
    email: string;
    department_name: string;
    tasks_completed: number;
    kpi_score: number;
  }[];
  recent_activities: { id: number; action: string; description: string; time_ago: string }[];
  ai_insights: string;
}

export const getDashboardData = () => apiRequest<DashboardData>('/dashboard/');