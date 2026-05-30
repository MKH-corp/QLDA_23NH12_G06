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

export const getRecentActivities = (page = 1, pageSize = 10) =>
  apiRequest<{ total: number; data: ActivityLog[]; page: number; page_size: number; pages: number }>(
    `/activities/recent?page=${page}&page_size=${pageSize}`,
  );
