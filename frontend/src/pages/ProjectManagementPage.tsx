// src/pages/ProjectManagementPage.tsx
import { useState, useEffect, useCallback } from 'react';
import {
  getProjects, getProjectDashboard, createProject, updateProject, deleteProject,
} from '../api/projects';
import { ProjectListItem, ProjectCreate, DashboardSummary, ProjectStatus } from '../types/project';
import { ProjectDetailModal } from '../components/project/ProjectDetailModal';
import { ProjectFormModal } from '../components/project/ProjectFormModal';
import { useAuth } from '../context/AuthContext';

const STATUS_COLORS: Record<string, string> = {
  PLANNING:  '#6366f1', ACTIVE: '#10b981', ON_HOLD: '#f59e0b',
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
  const [searchTerm,  setSearchTerm]  = useState('');
  const [selectedId,  setSelectedId]  = useState<number | null>(null);
  const [isFormOpen,  setIsFormOpen]  = useState(false);
  const [editProject, setEditProject] = useState<ProjectListItem | null>(null);
  const [toast,       setToast]       = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  };

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [pList, dash] = await Promise.all([
        getProjects({ status: statusFilter || undefined }),
        getProjectDashboard(),
      ]);
      setProjects(pList);
      setDashboard(dash);
    } catch (e: any) {
      setError(e.message || 'Lỗi tải dữ liệu');
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { load(); }, [load]);

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
    if (!confirm(`Xóa project "${p.name}"?`)) return;
    try {
      await deleteProject(p.id);
      showToast('✅ Đã xóa project');
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1600px', margin: '0 auto' }}>

      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', top: 24, right: 24, zIndex: 9999,
          background: '#dcfce7', color: '#166534', borderRadius: 12,
          padding: '12px 20px', fontWeight: 600, boxShadow: '0 4px 20px rgba(0,0,0,.1)',
        }}>{toast}</div>
      )}

      {/* ── Header ──────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h2 style={{ margin: 0, color: '#1e3a8a', fontSize: 26 }}>📁 Quản lý Dự án</h2>
          <p style={{ margin: '4px 0 0', color: '#64748b' }}>
            Theo dõi tiến độ, nhân sự, KPI toàn bộ dự án
          </p>
        </div>
        <button className="btn-gradient" onClick={() => { setEditProject(null); setIsFormOpen(true); }}>
          + Tạo Dự án
        </button>
      </div>

      {/* ── Dashboard summary cards ─────────────────────────────────── */}
      {dashboard && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 16, marginBottom: 24 }}>
          {[
            { label: 'Tổng dự án',      value: dashboard.total_projects,   icon: '📁', color: '#3b82f6' },
            { label: 'Đang hoạt động',  value: dashboard.active_projects,  icon: '🚀', color: '#10b981' },
            { label: 'Quá hạn',         value: dashboard.overdue_projects, icon: '⚠️', color: '#ef4444' },
            { label: 'Tiến độ TB',      value: `${dashboard.avg_progress}%`, icon: '📈', color: '#8b5cf6' },
            { label: 'Hoàn thành',      value: dashboard.status_breakdown?.COMPLETED || 0, icon: '✅', color: '#22c55e' },
          ].map(card => (
            <div key={card.label} className="glass-panel" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ fontSize: 28 }}>{card.icon}</div>
              <div>
                <div style={{ fontSize: 13, color: '#64748b' }}>{card.label}</div>
                <div style={{ fontSize: 24, fontWeight: 800, color: card.color }}>{card.value}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Filters ─────────────────────────────────────────────────── */}
      <div className="glass-panel" style={{ display: 'flex', gap: 12, marginBottom: 20, padding: '14px 20px', alignItems: 'center' }}>
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
          {['PLANNING','ACTIVE','ON_HOLD','REVIEW','COMPLETED','CANCELLED','ARCHIVED'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button className="btn-outline" onClick={load}>🔄 Tải lại</button>
      </div>

      {error && (
        <div style={{ background: '#fee2e2', color: '#991b1b', borderRadius: 10, padding: 12, marginBottom: 16 }}>
          ❌ {error}
        </div>
      )}

      {/* ── Project Cards Grid ─────────────────────────────────────── */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#64748b' }}>
          <div className="loading">Đang tải dự án...</div>
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
          <div style={{ fontSize: 48 }}>📭</div>
          <p>Không tìm thấy dự án nào.</p>
          <button className="btn-gradient" onClick={() => setIsFormOpen(true)}>
            + Tạo dự án đầu tiên
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 20 }}>
          {filtered.map(p => (
            <ProjectCard
              key={p.id} project={p}
              onOpen={() => setSelectedId(p.id)}
              onEdit={() => { setEditProject(p); setIsFormOpen(true); }}
              onDelete={() => handleDelete(p)}
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

  return (
    <div
      className="glass-panel"
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
        <span>✅ {p.completed_tasks}/{p.total_tasks} task</span>
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
            title={canDelete ? 'Delete project' : 'Only admins can delete projects'}
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
