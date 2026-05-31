import { apiRequest } from './client';
import { 
  ProjectCreate, ProjectUpdate, ProjectAnalytics, 
  ProjectListItem, DashboardSummary, ProjectOverview,
  ProjectMember, MemberRole, Milestone, KpiContribution, MyProject, TeamWorkload,
  AssignableUser, TaskSummary, ProjectReport,
} from '../types/project';

// Lưu ý: Thêm prefix /api/v1 nếu backend của bạn mount router ở /api/v1
const BASE_PATH = '/projects'; 
const COLLECTION_PATH = `${BASE_PATH}/`;

// ── Projects ──────────────────────────────────────────────────────────────

export const projectApi = {
  // GET: Lấy danh sách
  getAll: (params?: { status?: string; departmentId?: number; managerId?: number; skip?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set('status', params.status);
    if (params?.departmentId) q.set('department_id', String(params.departmentId));
    if (params?.managerId) q.set('manager_id', String(params.managerId));
    if (params?.skip) q.set('skip', String(params.skip));
    if (params?.limit) q.set('limit', String(params.limit));
    const qs = q.toString() ? `?${q.toString()}` : '';
    return apiRequest<ProjectListItem[]>(`${COLLECTION_PATH}${qs}`);
  },

  // GET: Lấy chi tiết 1 dự án
  getById: (id: number) => 
    apiRequest<ProjectOverview>(`${BASE_PATH}/${id}`),

  // POST: Tạo mới
  create: (data: ProjectCreate) => 
    apiRequest<ProjectListItem>(COLLECTION_PATH, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // PUT: Cập nhật dự án
  update: (id: number, data: ProjectUpdate) => 
    apiRequest<ProjectListItem>(`${BASE_PATH}/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // DELETE: Xóa dự án
  delete: (id: number) => 
    apiRequest<void>(`${BASE_PATH}/${id}`, {
      method: 'DELETE',
    }),

  // GET: Lấy thống kê tiến độ
  getAnalytics: (id: number) => 
    apiRequest<ProjectAnalytics>(`${BASE_PATH}/${id}/analytics`),

  // GET: Dashboard summary
  getDashboard: () =>
    apiRequest<DashboardSummary>(`${BASE_PATH}/dashboard`),

  // GET: KPI contribution
  getKpi: (id: number) =>
    apiRequest<KpiContribution>(`${BASE_PATH}/${id}/kpi`),

  getReport: (id: number) =>
    apiRequest<ProjectReport>(`${BASE_PATH}/${id}/report`),
};

// ── Members ────────────────────────────────────────────────────────────────

export const addMember = (projectId: number, userId: number, role: MemberRole) =>
  apiRequest<ProjectMember>(`${BASE_PATH}/${projectId}/members`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, role }),
  });

export const getProjectMembers = (projectId: number) =>
  apiRequest<ProjectMember[]>(`${BASE_PATH}/${projectId}/members`);

export const getAssignableUsers = (projectId: number) =>
  apiRequest<AssignableUser[]>(`${BASE_PATH}/${projectId}/assignable-users`);

export const getProjectTasks = (projectId: number) =>
  apiRequest<TaskSummary[]>(`${BASE_PATH}/${projectId}/tasks`);

export const addProjectMember = (
  projectId: number,
  payload: { user_id: number; role: MemberRole; contribution_share?: number; is_active?: boolean },
) =>
  apiRequest<ProjectMember>(`${BASE_PATH}/${projectId}/members`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

export const removeMember = (projectId: number, userId: number) =>
  apiRequest<void>(`${BASE_PATH}/${projectId}/members/${userId}`, {
    method: 'DELETE',
  });

export const updateMemberRole = (projectId: number, userId: number, role: MemberRole) =>
  apiRequest<ProjectMember>(`${BASE_PATH}/${projectId}/members/${userId}`, {
    method: 'PUT',
    body: JSON.stringify({ role }),
  });

export const updateProjectMember = (
  projectId: number,
  userId: number,
  payload: { role?: MemberRole; contribution_share?: number; is_active?: boolean },
) =>
  apiRequest<ProjectMember>(`${BASE_PATH}/${projectId}/members/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });

export const getMyProjects = () => apiRequest<MyProject[]>('/me/projects');
export const getMyProject = (projectId: number) => apiRequest<MyProject>(`/me/projects/${projectId}`);
export const getMyTasks = (projectId?: number) =>
  apiRequest<TaskSummary[]>(`/me/tasks${projectId ? `?project_id=${projectId}` : ''}`);
export const getManagerProjects = () => apiRequest<ProjectListItem[]>('/manager/projects');
export const getTeamWorkload = () => apiRequest<TeamWorkload[]>('/manager/team-workload');

// ── Milestones ─────────────────────────────────────────────────────────────

export const createMilestone = (projectId: number, data: {
  title: string; description?: string; due_date?: string; weight?: number;
}) =>
  apiRequest<Milestone>(`${BASE_PATH}/${projectId}/milestones`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const completeMilestone = (projectId: number, milestoneId: number) =>
  apiRequest<Milestone>(`${BASE_PATH}/${projectId}/milestones/${milestoneId}/complete`, {
    method: 'PATCH',
  });

export const updateMilestone = (
  projectId: number,
  milestoneId: number,
  data: { title?: string; description?: string; due_date?: string; weight?: number },
) =>
  apiRequest<Milestone>(`${BASE_PATH}/${projectId}/milestones/${milestoneId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const deleteMilestone = (projectId: number, milestoneId: number) =>
  apiRequest<void>(`${BASE_PATH}/${projectId}/milestones/${milestoneId}`, {
    method: 'DELETE',
  });

// ── Exports for backward compatibility ────────────────────────────────────

export const getProjects = projectApi.getAll;
export const getProjectDashboard = projectApi.getDashboard;
export const getProjectById = projectApi.getById;
export const createProject = projectApi.create;
export const updateProject = projectApi.update;
export const deleteProject = projectApi.delete;
export const getProjectAnalytics = projectApi.getAnalytics;
export const getProjectKpi = projectApi.getKpi;
export const getProjectReport = projectApi.getReport;
