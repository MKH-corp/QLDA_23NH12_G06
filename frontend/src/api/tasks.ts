import { apiRequest } from './client';
import type { PageResponse } from './pagination';
import type { Task, TaskFormValues, TaskPayload } from '../types/task';
import { apiStatusToBoardStatus, boardStatusToApiStatus, normalizeTask } from '../utils/task';

interface BackendTask {
  id: number;
  title: string;
  description?: string | null;
  status: 'todo' | 'doing' | 'blocked' | 'done';
  deadline?: string | null;
  done_at?: string | null;
  base_weight: number;
  creator_id: number;
  assignee_id: number;
  department_id: number;
  project_id?: number | null;
}

function mapBackendTask(task: BackendTask): Task {
  return normalizeTask({
    ...task,
    status: apiStatusToBoardStatus(task.status),
  });
}

function toCreatePayload(values: TaskFormValues): TaskPayload {
  return {
    title: values.title,
    description: values.description || undefined,
    status: boardStatusToApiStatus(values.status),
    deadline: values.deadline || null,
    base_weight: Number(values.base_weight),
    assignee_id: Number(values.assignee_id),
    department_id: Number(values.department_id),
    project_id: values.project_id ?? null,
  };
}

function toUpdatePayload(values: TaskFormValues): Partial<TaskPayload> {
  return {
    title: values.title,
    description: values.description || undefined,
    status: boardStatusToApiStatus(values.status),
    deadline: values.deadline || null,
    base_weight: Number(values.base_weight),
    assignee_id: Number(values.assignee_id),
    department_id: Number(values.department_id),
    project_id: values.project_id ?? null,
  };
}

export async function getTasks(filters?: { status?: string; overdue?: boolean; assigneeId?: number; page?: number; pageSize?: number }): Promise<PageResponse<Task>> {
  const params = new URLSearchParams();
  if (filters?.status) params.set('status', filters.status);
  if (typeof filters?.overdue === 'boolean') params.set('overdue', String(filters.overdue));
  if (filters?.assigneeId) params.set('assignee_id', String(filters.assigneeId));
  params.set('page', String(filters?.page ?? 1));
  params.set('page_size', String(filters?.pageSize ?? 20));
  const query = params.toString() ? `?${params.toString()}` : '';

  const data = await apiRequest<PageResponse<BackendTask>>(`/tasks${query}`);
  return { ...data, items: data.items.map(mapBackendTask) };
}

export async function getTask(taskId: number): Promise<Task> {
  const data = await apiRequest<BackendTask>(`/tasks/${taskId}`);
  return mapBackendTask(data);
}

export async function createTask(values: TaskFormValues): Promise<Task> {
  const data = await apiRequest<BackendTask>('/tasks', {
    method: 'POST',
    body: JSON.stringify(toCreatePayload(values)),
  });
  return mapBackendTask(data);
}

export async function updateTask(taskId: number, values: TaskFormValues): Promise<Task> {
  const data = await apiRequest<BackendTask>(`/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify(toUpdatePayload(values)),
  });
  return mapBackendTask(data);
}

export async function updateTaskStatus(taskId: number, status: Task['status']): Promise<Task> {
  const data = await apiRequest<BackendTask>(`/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify({ status: boardStatusToApiStatus(status) }),
  });
  return mapBackendTask(data);
}

export function deleteTask(taskId: number): Promise<void> {
  return apiRequest<void>(`/tasks/${taskId}`, {
    method: 'DELETE',
  });
}

