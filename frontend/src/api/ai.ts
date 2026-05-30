import { apiRequest } from './client';

export interface AIEvidence {
  kpi_score?: number | null;
  task_ids: number[];
  overdue_count: number;
  near_deadline_count: number;
  blocked_count: number;
  tasks_completed?: number;
}

export interface AIInsight {
  type: 'warning' | 'info' | 'success' | 'danger';
  title: string;
  message: string;
  severity: 'info' | 'success' | 'warning' | 'danger';
  recommendations: string[];
  evidence: AIEvidence;
}

export interface AIDashboardSummary {
  user_id: number;
  role: string;
  total_kpi_score?: number | null;
  total_tasks_completed: number;
  overdue_tasks: number;
  near_deadline_tasks: number;
  blocked_tasks: number;
  risk_users: Array<{ user_id: number; name: string; kpi: number; department?: string }>;
  top_performers: Array<{ user_id: number; name: string; kpi: number; department?: string }>;
  team_overdue_count: number;
  recommendations: string[];
}

export interface AIChatResponse {
  reply: string;
  insights: string[];
  used_fallback: boolean;
  evidence: Record<string, any>;
}

export interface AIChatMessage {
  role: 'assistant' | 'user';
  content: string;
}

export const getMyAIInsights = () => apiRequest<AIInsight[]>('/ai/insights/me');
export const getTeamAIInsights = () => apiRequest<AIInsight[]>('/ai/insights/team');
export const runAIInsights = () =>
  apiRequest<{ message: string; users_processed: number | string }>('/ai/insights/run', {
    method: 'POST',
  });
export const getAIDashboardSummary = () => apiRequest<AIDashboardSummary>('/ai/summary/dashboard');
export const chatWithAI = (message: string, history: AIChatMessage[] = []) =>
  apiRequest<AIChatResponse>('/ai/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history }),
  });
