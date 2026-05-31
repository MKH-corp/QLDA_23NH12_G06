// src/pages/ProjectManagementPage.tsx
import { useState, useEffect, useCallback } from 'react';
import {
  getProjects, getProjectDashboard, createProject, updateProject, deleteProject,
} from '../api/projects';
import { ProjectListItem, ProjectCreate, DashboardSummary, ProjectStatus } from '../types/project';
import { ProjectDetailModal } from '../components/project/ProjectDetailModal';
import { ProjectFormModal } from '../components/project/ProjectFormModal';
import { useAuth } from '../context/AuthContext';
import { getDepartments, getUsers } from '../api/references';
import type { DepartmentOption, UserOption } from '../types/reference';
import { ConfirmModal, EmptyState, Icon, Skeleton, StatCard, type IconName } from '../components/ui';

const STATUS_COLORS: Record<string, string> = {
  PLANNING:  '#6366f1', ACTIVE: '#10b981', PAUSED: '#f59e0b', ON_HOLD: '#f59e0b',
  REVIEW:    '#3b82f6', COMPLETED: '#22c55e',
  CANCELLED: '#ef4444', ARCHIVED:  '#94a3b8',
};

const PRIORITY_COLORS: Record<string, string> = {
  LOW: '#10b981', MEDIUM: '#f59e0b', HIGH: '#ef4444', CRITICAL: '#7c3aed',
};

export function ProjectManagementPage() {
  const { user } = useAuth();
  const [projects,    setProjects]    = useState<ProjectListItem[]>([]);
  const [dashboard,   setDashboard]   = useState<DashboardSummary | null>(null);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [managerFilter, setManagerFilter] = useState('');
  const [searchTerm,  setSearchTerm]  = useState('');
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [managers, setManagers] = useState<UserOption[]>([]);
  const [selectedId,  setSelectedId]  = useState<number | null>(null);
  const [isFormOpen,  setIsFormOpen]  = useState(false);
  const [editProject, setEditProject] = useState<ProjectListItem | null>(null);
  const [projectToDelete, setProjectToDelete] = useState<ProjectListItem | null>(null);
  const [toast,       setToast]       = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [pList, dash] = await Promise.all([
        getProjects({
          status: statusFilter || undefined,
          departmentId: departmentFilter ? Number(departmentFilter) : undefined,
          managerId: managerFilter ? Number(managerFilter) : undefined,
        }),
        getProjectDashboard(),
      ]);
      setProjects(pList);
      setDashboard(dash);
    } catch (e: any) {
      setError(e.message || 'Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  }, [departmentFilter, managerFilter, statusFilter]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    Promise.all([getDepartments(), getUsers()])
      .then(([departmentData, userData]) => {
        setDepartments(departmentData);
        setManagers(userData.filter(item => item.role === 'manager' || item.role === 'admin'));
      })
      .catch(() => {
        setDepartments([]);
        setManagers([]);
      });
  }, []);

  const filtered = projects.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.code || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreate = async (data: ProjectCreate) => {
    await createProject(data);
    showToast('✅ Tạo project thành công!');
    load();
  };

  const handleUpdate = async (data: ProjectCreate) => {
    if (!editProject) return;
    await updateProject(editProject.id, data);
    showToast('✅ Cập nhật project thành công!');
    load();
  };

  const handleDelete = async (p: ProjectListItem) => {
    try {
      await deleteProject(p.id);
      showToast(p.total_tasks > 0 ? 'Đã archive project' : 'Đã xóa project');
      setProjectToDelete(null);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div className="project-management-page">

      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', top: 24, right: 24, zIndex: 9999,
          background: '#dcfce7', color: '#166534', borderRadius: 12,
          padding: '12px 20px', fontWeight: 600, boxShadow: '0 4px 20px rgba(0,0,0,.1)',
        }}>{toast}</div>
      )}

      {/* ── Header ──────────────────────────────────────────────────── */}
      <div className="page-heading">
        <div>
          <p className="eyebrow">Danh mục dự án</p>
          <h1>Quản lý dự án</h1>
          <p className="subtitle">
            Theo dõi tiến độ, nhân sự, KPI toàn bộ dự án
          </p>
        </div>
        <button className="btn-gradient" onClick={() => { setEditProject(null); setIsFormOpen(true); }}>
          <Icon name="plus" size={16} /> Tạo dự án
        </button>
      </div>

      {/* ── Dashboard summary cards ─────────────────────────────────── */}
      {dashboard && (
        <div className="project-summary-grid">
          {[
            { label: 'Tổng dự án', value: dashboard.total_projects, icon: 'folder', tone: 'blue' },
            { label: 'Đang hoạt động', value: dashboard.active_projects, icon: 'activity', tone: 'green' },
            { label: 'Quá hạn', value: dashboard.overdue_projects, icon: 'alert', tone: 'red' },
            { label: 'Tiến độ TB', value: `${dashboard.avg_progress}%`, icon: 'kpi', tone: 'purple' },
            { label: 'Hoàn thành', value: dashboard.status_breakdown?.COMPLETED || 0, icon: 'check', tone: 'green' },
          ].map(card => (
            <StatCard key={card.label} icon={card.icon as IconName} label={card.label} tone={card.tone as 'blue' | 'green' | 'purple' | 'red'} value={card.value} />
          ))}
        </div>
      )}

      {/* ── Filters ─────────────────────────────────────────────────── */}
      <div className="glass-panel project-filter-toolbar">
        <div style={{ flex: 1, display: 'flex', gap: 8, background: '#f1f5f9', borderRadius: 99, padding: '8px 14px', alignItems: 'center' }}>
          <span>🔍</span>
          <input
            style={{ border: 'none', background: 'transparent', outline: 'none', width: '100%' }}
            placeholder="Tìm theo tên, mã dự án..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #e2e8f0' }}
        >
          <option value="">Tất cả trạng thái</option>
          {['PLANNING','ACTIVE','PAUSED','ON_HOLD','REVIEW','COMPLETED','CANCELLED','ARCHIVED'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={departmentFilter}
          onChange={e => setDepartmentFilter(e.target.value)}
          style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #e2e8f0' }}
        >
          <option value="">Tất cả phòng ban</option>
          {departments.map(department => (
            <option key={department.id} value={department.id}>{department.name}</option>
          ))}
        </select>
        <select
          value={managerFilter}
          onChange={e => setManagerFilter(e.target.value)}
          style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #e2e8f0' }}
        >
          <option value="">Tất cả manager</option>
          {managers.map(manager => (
            <option key={manager.id} value={manager.id}>{manager.full_name}</option>
          ))}
        </select>
        <button className="btn-outline" onClick={load}><Icon name="refresh" size={15} /> Tải lại</button>
      </div>

      {error && (
        <div style={{ background: '#fee2e2', color: '#991b1b', borderRadius: 10, padding: 12, marginBottom: 16 }}>
          ❌ {error}
        </div>
      )}

      {/* ── Project Cards Grid ─────────────────────────────────────── */}
      {loading ? (
        <Skeleton rows={4} />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="Không tìm thấy dự án"
          description="Điều chỉnh bộ lọc hoặc tạo dự án đầu tiên để bắt đầu theo dõi tiến độ."
          action={<button className="btn-gradient" onClick={() => setIsFormOpen(true)}><Icon name="plus" size={15} /> Tạo dự án</button>}
        />
      ) : (
        <div className="project-card-grid">
          {filtered.map(p => (
            <ProjectCard
              key={p.id} project={p}
              onOpen={() => setSelectedId(p.id)}
              onEdit={() => { setEditProject(p); setIsFormOpen(true); }}
              onDelete={() => setProjectToDelete(p)}
              canDelete={user?.role === 'admin'}
            />
          ))}
        </div>
      )}

      {/* ── Modals ──────────────────────────────────────────────────── */}
      {selectedId && (
        <ProjectDetailModal
          projectId={selectedId}
          onClose={() => { setSelectedId(null); load(); }}
        />
      )}

      {isFormOpen && (
        <ProjectFormModal
          project={editProject}
          onClose={() => { setIsFormOpen(false); setEditProject(null); }}
          onSubmit={editProject ? handleUpdate : handleCreate}
        />
      )}

      <ConfirmModal
        open={projectToDelete != null}
        title={projectToDelete?.total_tasks ? 'Lưu trữ dự án?' : 'Xóa dự án?'}
        description={projectToDelete?.total_tasks
          ? `Dự án "${projectToDelete.name}" đã có task và sẽ được chuyển sang lưu trữ.`
          : `Dự án "${projectToDelete?.name ?? ''}" sẽ bị xóa khỏi hệ thống.`}
        onCancel={() => setProjectToDelete(null)}
        onConfirm={() => projectToDelete ? void handleDelete(projectToDelete) : undefined}
      />
    </div>
  );
}

// ── ProjectCard component ──────────────────────────────────────────────────
function ProjectCard({ project: p, onOpen, onEdit, onDelete, canDelete }: {
  project: ProjectListItem;
  onOpen: () => void; onEdit: () => void; onDelete: () => void; canDelete: boolean;
}) {
  const statusColor   = STATUS_COLORS[p.status]   || '#64748b';
  const priorityColor = PRIORITY_COLORS[p.priority] || '#64748b';
  const pct = Math.round(p.progress_percentage);
  const taskPct = Math.round(p.task_completion_percentage);

  return (
    <div
      className="glass-panel project-card"
      style={{ cursor: 'pointer', transition: 'transform .15s', position: 'relative' }}
      onClick={onOpen}
    >
      {p.is_overdue && (
        <div style={{
          position: 'absolute', top: -8, right: 12,
          background: '#ef4444', color: 'white',
          fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 99,
        }}>QUÁ HẠN</div>
      )}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, letterSpacing: 1 }}>
            {p.code || '—'}
          </div>
          <div style={{ fontWeight: 700, fontSize: 16, color: '#0f172a', marginTop: 2 }}>{p.name}</div>
        </div>
        <span style={{
          background: statusColor + '22', color: statusColor,
          padding: '3px 10px', borderRadius: 99, fontSize: 11, fontWeight: 700,
        }}>{p.status}</span>
      </div>

      {/* Progress bar */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#64748b', marginBottom: 4 }}>
          <span>Tiến độ</span><span style={{ fontWeight: 700, color: '#0f172a' }}>{pct}%</span>
        </div>
        <div style={{ background: '#e2e8f0', borderRadius: 99, height: 8, overflow: 'hidden' }}>
          <div style={{
            width: `${pct}%`, height: '100%', borderRadius: 99,
            background: pct >= 80 ? '#22c55e' : pct >= 50 ? '#3b82f6' : '#f59e0b',
            transition: 'width .5s',
          }} />
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', gap: 12, fontSize: 12, color: '#64748b', marginBottom: 14 }}>
        <span>✅ {p.completed_tasks}/{p.total_tasks} task ({taskPct}%)</span>
        {p.overdue_tasks > 0 && <span style={{ color: '#ef4444' }}>⚠️ {p.overdue_tasks} quá hạn</span>}
        <span>👥 {p.member_count}</span>
        <span>🎯 {p.milestones_done}/{p.milestone_count} milestone</span>
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontSize: 11, color: '#94a3b8' }}>
          {p.department_name && <span>🏢 {p.department_name}</span>}
          {p.manager_name && <span style={{ marginLeft: 8 }}>👤 {p.manager_name}</span>}
        </div>
        <div style={{ display: 'flex', gap: 6 }} onClick={e => e.stopPropagation()}>
          <button
            className="btn-outline"
            style={{ padding: '4px 10px', fontSize: 12 }}
            onClick={onEdit}
          >✏️</button>
          <button
            className="btn-outline"
            style={{ padding: '4px 10px', fontSize: 12, color: '#ef4444', borderColor: '#fca5a5' }}
            disabled={!canDelete}
            title={canDelete ? 'Xóa dự án' : 'Chỉ admin được xóa dự án'}
            onClick={canDelete ? onDelete : undefined}
          >🗑️</button>
        </div>
      </div>

      {/* Priority tag */}
      <div style={{ position: 'absolute', bottom: 12, left: 20, display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{
          fontSize: 10, fontWeight: 700, color: priorityColor,
          background: priorityColor + '18', padding: '2px 8px', borderRadius: 99,
        }}>{p.priority}</span>
        {p.start_date && <span style={{ fontSize: 11, color: '#94a3b8' }}>{new Date(p.start_date).toLocaleDateString('vi-VN')} -</span>}
        {p.end_date && (
          <span style={{ fontSize: 11, color: '#94a3b8' }}>
            📅 {new Date(p.end_date).toLocaleDateString('vi-VN')}
          </span>
        )}
      </div>
      <div style={{ height: 8 }} />
    </div>
  );
}
