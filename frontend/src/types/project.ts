// ── Types ──────────────────────────────────────────────────────────────────

export type ProjectStatus =
  | 'PLANNING' | 'ACTIVE' | 'PAUSED' | 'ON_HOLD' | 'REVIEW'
  | 'COMPLETED' | 'CANCELLED' | 'ARCHIVED';

export type ProjectPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type MemberRole = 'PROJECT_MANAGER' | 'TEAM_LEAD' | 'MEMBER' | 'VIEWER';

export interface ProjectListItem {
  id: number;
  name: string;
  description?: string | null;
  code: string | null;
  status: ProjectStatus;
  priority: ProjectPriority;
  progress_percentage: number;
  start_date: string | null;
  end_date: string | null;
  estimated_hours: number | null;
  estimated_budget: number | null;
  department_id: number | null;
  manager_id: number | null;
  department_name: string;
  manager_name: string;
  total_tasks: number;
  completed_tasks: number;
  done_tasks: number;
  task_completion_percentage: number;
  project_progress_percentage: number;
  overdue_tasks: number;
  member_count: number;
  total_members: number;
  milestone_count: number;
  milestones_done: number;
  is_overdue: boolean;
  project_weight: number;
}

export interface ProjectMember {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  role: MemberRole;
  contribution_share: number;
  is_active: boolean;
  joined_at: string;
}

export interface Milestone {
  id: number;
  title: string;
  description: string | null;
  due_date: string | null;
  is_completed: boolean;
  completed_at: string | null;
  weight: number;
}

export interface TaskSummary {
  id: number;
  title: string;
  status: string;
  priority: string;
  deadline: string | null;
  done_at: string | null;
  base_weight: number;
  assignee_id: number | null;
  assignee_name: string;
  project_id: number | null;
  department_id: number | null;
  is_overdue: boolean;
}

export interface AssignableUser {
  id: number;
  full_name: string;
  email: string;
  department_id: number;
  project_role: MemberRole;
}

export interface StatusHistoryItem {
  id: number;
  from_status: string | null;
  to_status: string;
  actor_name: string;
  reason: string | null;
  changed_at: string;
}

export interface AuditLogItem {
  id: number;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  actor_name: string;
  changed_at: string;
}

export interface ProjectAnalytics {
  progress_percentage: number;
  project_progress_percentage: number;
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  doing_tasks: number;
  blocked_tasks: number;
  review_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
  task_completion_percentage: number;
  done_tasks: number;
  todo_tasks: number;
  on_time_rate: number;
  velocity: number;
  estimated_hours: number | null;
  actual_hours: number;
  budget_utilization: number | null;
  milestone_progress: number;
  total_members: number;
  total_milestones: number;
  completed_milestones: number;
  milestone_completion_percentage: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_indicators: string[];
}

export interface ProjectMemberPerformance {
  user_id: number;
  full_name: string;
  email: string;
  department_name: string;
  project_role: MemberRole;
  contribution_share: number;
  total_tasks: number;
  done_tasks: number;
  overdue_tasks: number;
  task_completion_percentage: number;
  kpi_score: number;
}

export interface ProjectReport {
  analytics: ProjectAnalytics;
  task_status_breakdown: Record<string, number>;
  member_performance: ProjectMemberPerformance[];
  top_contributor: ProjectMemberPerformance | null;
  most_overdue_member: ProjectMemberPerformance | null;
}

export interface KpiContribution {
  total_score_contributed: number;
  tasks_completed: number;
  tasks_overdue: number;
  milestones_completed: number;
  on_time_rate: number;
  member_contributions: Array<{
    user_id: number;
    full_name: string;
    role: string;
    kpi_score: number;
  }>;
}

export interface ProjectOverview {
  id: number;
  name: string;
  code: string | null;
  description: string | null;
  status: ProjectStatus;
  priority: ProjectPriority;
  progress_percentage: number;
  start_date: string | null;
  end_date: string | null;
  estimated_hours: number | null;
  actual_hours: number;
  estimated_budget: number | null;
  project_weight: number;
  department_id: number | null;
  manager_id: number | null;
  department_name: string;
  manager_name: string;
  created_at: string | null;
  updated_at: string | null;
  members: ProjectMember[];
  milestones: Milestone[];
  recent_tasks: TaskSummary[];
  status_history: StatusHistoryItem[];
  recent_audit_logs: AuditLogItem[];
  analytics: ProjectAnalytics | null;
  kpi_contribution: KpiContribution | null;
}

export interface ProjectCreate {
  name: string;
  code?: string;
  description?: string;
  status?: ProjectStatus;
  priority?: ProjectPriority;
  department_id?: number;
  manager_id?: number;
  start_date?: string;
  end_date?: string;
  estimated_hours?: number;
  estimated_budget?: number;
  project_weight?: number;
}

export interface ProjectUpdate extends Partial<ProjectCreate> {
  reason?: string;
}

export interface DashboardSummary {
  total_projects: number;
  status_breakdown: Record<string, number>;
  overdue_projects: number;
  avg_progress: number;
  active_projects: number;
}

export interface MyProject {
  project_id: number;
  project_code: string | null;
  project_name: string;
  description: string | null;
  department: string;
  project_status: ProjectStatus;
  project_role: MemberRole | null;
  contribution_share: number;
  start_date: string | null;
  due_date: string | null;
  progress: number;
  project_health: 'OK' | 'AT_RISK' | 'OVERDUE' | 'COMPLETED' | string;
  assigned_tasks: number;
  doing_tasks: number;
  review_tasks: number;
  done_tasks: number;
  overdue_tasks: number;
}

export interface TeamWorkload {
  user_id: number;
  full_name: string;
  email: string;
  active_projects: number;
  assigned_tasks: number;
  doing_tasks: number;
  review_tasks: number;
  overdue_tasks: number;
  estimated_hours: number;
  actual_hours: number;
  workload_status: string;
}
