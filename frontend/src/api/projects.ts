import { apiRequest } from './client';
import { 
  ProjectCreate, ProjectUpdate, ProjectAnalytics, 
  ProjectListItem, DashboardSummary, ProjectOverview,
  ProjectMember, MemberRole, Milestone, KpiContribution 
} from '../types/project';

// Lưu ý: Thêm prefix /api/v1 nếu backend của bạn mount router ở /api/v1
const BASE_PATH = '/projects'; 
const COLLECTION_PATH = `${BASE_PATH}/`;

// ── Projects ──────────────────────────────────────────────────────────────

export const projectApi = {
  // GET: Lấy danh sách
  getAll: (params?: { status?: string; skip?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set('status', params.status);
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
};

// ── Members ────────────────────────────────────────────────────────────────

export const addMember = (projectId: number, userId: number, role: MemberRole) =>
  apiRequest<ProjectMember>(`${BASE_PATH}/${projectId}/members`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, role }),
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

// ── Exports for backward compatibility ────────────────────────────────────

export const getProjects = projectApi.getAll;
export const getProjectDashboard = projectApi.getDashboard;
export const getProjectById = projectApi.getById;
export const createProject = projectApi.create;
export const updateProject = projectApi.update;
export const deleteProject = projectApi.delete;
export const getProjectAnalytics = projectApi.getAnalytics;
export const getProjectKpi = projectApi.getKpi;
