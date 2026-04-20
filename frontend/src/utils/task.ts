import type { ApiTaskStatus, BoardStatus, Task, TaskFormValues } from '../types/task';

const priorityMap: Record<number, Task['priority']> = {
  1: 'Low',
  2: 'Medium',
  3: 'High',
};

export function inferPriority(baseWeight: number): Task['priority'] {
  if (baseWeight >= 4) return 'High';
  if (baseWeight >= 2) return 'Medium';
  return 'Low';
}

export function apiStatusToBoardStatus(status: ApiTaskStatus): BoardStatus {
  return status;
}

export function boardStatusToApiStatus(status: BoardStatus): ApiTaskStatus {
  return status;
}

export function normalizeTask(task: Omit<Task, 'priority' | 'due_date'>): Task {
  return {
    ...task,
    due_date: task.deadline ?? null,
    priority: priorityMap[task.base_weight] ?? inferPriority(task.base_weight),
  };
}

export function toTaskFormValues(task?: Task | null): TaskFormValues {
  return {
    title: task?.title ?? '',
    description: task?.description ?? '',
    status: task?.status ?? 'todo',
    deadline: task?.deadline ?? '',
    base_weight: task?.base_weight ?? 1,
    creator_id: task?.creator_id ?? 1,
    assignee_id: task?.assignee_id ?? 1,
    department_id: task?.department_id ?? 1,
  };
}
