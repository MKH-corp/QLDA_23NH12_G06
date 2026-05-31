export type BoardStatus = 'todo' | 'doing' | 'in_review' | 'blocked' | 'done';
export type ApiTaskStatus = 'todo' | 'doing' | 'in_review' | 'blocked' | 'done';

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
  reviewer_id?: number | null;
  department_id: number;
  project_id?: number | null;
  estimated_hours?: number | null;
  actual_hours?: number;
  priority: 'Low' | 'Medium' | 'High';
}

export interface TaskPayload {
  title: string;
  description?: string;
  status: ApiTaskStatus;
  deadline?: string | null;
  base_weight: number;
  assignee_id: number;
  reviewer_id?: number | null;
  department_id: number;
  project_id?: number | null;
  estimated_hours?: number | null;
  actual_hours?: number;
}

export interface TaskFormValues {
  title: string;
  description: string;
  status: BoardStatus;
  deadline: string;
  base_weight: number;
  assignee_id: number;
  department_id: number;
  project_id?: number | null;
}
