export type BoardStatus = 'todo' | 'doing' | 'blocked' | 'done';
export type ApiTaskStatus = 'todo' | 'doing' | 'blocked' | 'done';

export interface Task {
  id: number;
  title: string;
  description?: string | null;
  status: BoardStatus;
  deadline?: string | null;
  due_date?: string | null;
  done_at?: string | null;
  base_weight: number;
  creator_id: number;
  assignee_id: number;
  department_id: number;
  priority: 'Low' | 'Medium' | 'High';
}

export interface TaskPayload {
  title: string;
  description?: string;
  status: ApiTaskStatus;
  deadline?: string | null;
  base_weight: number;
  assignee_id: number;
  department_id: number;
}

export interface TaskFormValues {
  title: string;
  description: string;
  status: BoardStatus;
  deadline: string;
  base_weight: number;
  assignee_id: number;
  department_id: number;
}
