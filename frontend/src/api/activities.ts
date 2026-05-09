import { apiRequest } from './client';

export interface ActivityLog {
  id: number;
  user_id: number;
  user_name: string;
  action_type: string;
  entity_type: string;
  description: string;
  time_ago: string;
}

export const getRecentActivities = (limit = 10) => 
  apiRequest<{total: number, data: ActivityLog[]}>(`/activities/recent?limit=${limit}`);