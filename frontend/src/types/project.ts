// ── Types ──────────────────────────────────────────────────────────────────

export type ProjectStatus =
  | 'PLANNING' | 'ACTIVE' | 'ON_HOLD' | 'REVIEW'
  | 'COMPLETED' | 'CANCELLED' | 'ARCHIVED';

export type ProjectPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type MemberRole = 'PROJECT_MANAGER' | 'TEAM_LEAD' | 'MEMBER' | 'VIEWER';

export interface ProjectListItem {
  id: number;
  name: string;
  code: string | null;
  status: ProjectStatus;
  priority: ProjectPriority;
  progress_percentage: number;
  start_date: string | null;
  end_date: string | null;
  department_name: string;
  manager_name: string;
  total_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  member_count: number;
  milestone_count: number;
  milestones_done: number;
  is_overdue: boolean;
}

export interface ProjectMember {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  role: MemberRole;
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
  assignee_name: string;
  is_overdue: boolean;
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
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  doing_tasks: number;
  blocked_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
  on_time_rate: number;
  velocity: number;
  estimated_hours: number | null;
  actual_hours: number;
  budget_utilization: number | null;
  milestone_progress: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_indicators: string[];
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
