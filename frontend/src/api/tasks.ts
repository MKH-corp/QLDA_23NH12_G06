import type { Task, TaskFormValues, TaskPayload } from '../types/task';
import { apiStatusToBoardStatus, boardStatusToApiStatus, normalizeTask } from '../utils/task';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

interface BackendTask {
  id: number;
  title: string;
  description?: string | null;
  status: 'todo' | 'doing' | 'done';
  deadline?: string | null;
  done_at?: string | null;
  base_weight: number;
  creator_id: number;
  assignee_id: number;
  department_id: number;
}

function mapBackendTask(task: BackendTask): Task {
  return normalizeTask({
    ...task,
    status: apiStatusToBoardStatus(task.status),
  });
}

function toPayload(values: TaskFormValues): TaskPayload {
  return {
    title: values.title,
    description: values.description || undefined,
    status: boardStatusToApiStatus(values.status),
    deadline: values.deadline || null,
    base_weight: Number(values.base_weight),
    creator_id: Number(values.creator_id),
    assignee_id: Number(values.assignee_id),
    department_id: Number(values.department_id),
  };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || 'Request failed');
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function getTasks(): Promise<Task[]> {
  const data = await request<BackendTask[]>('/tasks');
  return data.map(mapBackendTask);
}

export async function createTask(values: TaskFormValues): Promise<Task> {
  const data = await request<BackendTask>('/tasks', {
    method: 'POST',
    body: JSON.stringify(toPayload(values)),
  });
  return mapBackendTask(data);
}

export async function updateTask(taskId: number, values: TaskFormValues): Promise<Task> {
  const data = await request<BackendTask>(`/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify(toPayload(values)),
  });
  return mapBackendTask(data);
}

export async function deleteTask(taskId: number): Promise<void> {
  await request<void>(`/tasks/${taskId}`, {
    method: 'DELETE',
  });
}
