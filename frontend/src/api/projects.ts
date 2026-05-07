import { apiRequest } from './client';

export interface Project {
  id: number;
  name: string;
  status: string;
  progress: number;
  total_tasks: number;
}

export const getProjects = () => apiRequest<Project[]>('/projects/');
export const createProject = (data: any) => apiRequest<Project>('/projects/', { method: 'POST', body: JSON.stringify(data) });