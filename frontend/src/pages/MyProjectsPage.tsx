import { useEffect, useMemo, useState } from 'react';

import { getMyProjects, getMyTasks } from '../api/projects';
import { useAuth } from '../context/AuthContext';
import type { MyProject, TaskSummary } from '../types/project';

export function MyProjectsPage() {
  const { user } = useAuth();
  const [projects, setProjects] = useState<MyProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    getMyProjects()
      .then(data => {
        if (mounted) setProjects(data);
      })
      .catch(reason => {
        if (mounted) setError(reason instanceof Error ? reason.message : 'Không tải được danh sách dự án');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const openProject = async (projectId: number) => {
    setSelectedProjectId(projectId);
    setTasksLoading(true);
    setError(null);
    try {
      setTasks(await getMyTasks(projectId));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Không tải được task của dự án');
      setTasks([]);
    } finally {
      setTasksLoading(false);
    }
  };

  const selectedProject = projects.find(project => project.project_id === selectedProjectId) ?? null;
  const filteredProjects = useMemo(() => projects.filter(project => {
    const search = searchTerm.trim().toLowerCase();
    const matchesSearch = !search
      || project.project_name.toLowerCase().includes(search)
      || (project.project_code || '').toLowerCase().includes(search)
      || project.department.toLowerCase().includes(search);
    return matchesSearch && (!statusFilter || project.project_status === statusFilter);
  }), [projects, searchTerm, statusFilter]);
  const summary = useMemo(() => ({
    total: projects.length,
    active: projects.filter(project => project.project_status === 'ACTIVE').length,
    assignedTasks: projects.reduce((sum, project) => sum + project.assigned_tasks, 0),
    overdueTasks: projects.reduce((sum, project) => sum + project.overdue_tasks, 0),
  }), [projects]);

  return (
    <div className="page my-projects-page">
      <div className="page-header my-projects-header">
        <div>
          <p className="eyebrow">My Projects</p>
          <h2>Dự án của tôi</h2>
          <p className="my-projects-subtitle">
            {user?.role === 'manager'
              ? 'Theo dõi các dự án bạn tham gia hoặc đang quản lý.'
              : 'Theo dõi dự án được phân công và công việc cá nhân.'}
          </p>
        </div>
      </div>

      <section className="my-project-summary">
        <SummaryCard label="Tổng dự án" value={summary.total} />
        <SummaryCard label="Đang hoạt động" value={summary.active} />
        <SummaryCard label="Task được giao" value={summary.assignedTasks} />
        <SummaryCard label="Task quá hạn" value={summary.overdueTasks} danger={summary.overdueTasks > 0} />
      </section>

      <section className="panel my-project-list-panel">
        <div className="panel__header my-project-toolbar">
          <div>
            <h3>Danh sách dự án</h3>
            <span>{filteredProjects.length} dự án phù hợp</span>
          </div>
          <div className="my-project-filters">
            <input
              value={searchTerm}
              onChange={event => setSearchTerm(event.target.value)}
              placeholder="Tìm tên, mã hoặc phòng ban"
            />
            <select value={statusFilter} onChange={event => setStatusFilter(event.target.value)}>
              <option value="">Tất cả trạng thái</option>
              {['PLANNING', 'ACTIVE', 'PAUSED', 'ON_HOLD', 'REVIEW', 'COMPLETED', 'CANCELLED', 'ARCHIVED'].map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? <div className="panel-empty">Đang tải dự án...</div> : null}
        {error ? <div className="error-box">{error}</div> : null}
        {!loading && !error && projects.length === 0 ? (
          <div className="panel-empty">Bạn chưa được phân công vào dự án nào.</div>
        ) : null}
        {!loading && projects.length > 0 && filteredProjects.length === 0 ? (
          <div className="panel-empty">Không tìm thấy dự án phù hợp bộ lọc.</div>
        ) : null}
        {filteredProjects.length > 0 ? (
          <MyProjectTable
            projects={filteredProjects}
            selectedProjectId={selectedProjectId}
            onSelect={projectId => void openProject(projectId)}
          />
        ) : null}
      </section>

      {selectedProject ? (
        <section className="panel my-project-task-panel">
          <div className="panel__header">
            <div>
              <p className="eyebrow">{selectedProject.project_code || 'NO-CODE'}</p>
              <h3>Task của tôi: {selectedProject.project_name}</h3>
            </div>
            <button type="button" className="button-secondary" onClick={() => {
              setSelectedProjectId(null);
              setTasks([]);
            }}>Đóng</button>
          </div>
          {tasksLoading ? <div className="panel-empty">Đang tải task...</div> : null}
          {!tasksLoading && tasks.length === 0 ? <div className="panel-empty">Bạn chưa có task trong project này.</div> : null}
          {!tasksLoading && tasks.length > 0 ? <MyProjectTaskTable tasks={tasks} /> : null}
        </section>
      ) : null}
    </div>
  );
}

function MyProjectTable({
  projects,
  selectedProjectId,
  onSelect,
}: {
  projects: MyProject[];
  selectedProjectId: number | null;
  onSelect: (projectId: number) => void;
}) {
  return (
    <div className="table-wrap">
      <table className="data-table my-project-table">
        <thead>
          <tr>
            <th>Dự án</th>
            <th>Vai trò</th>
            <th>Phòng ban</th>
            <th>Deadline</th>
            <th>Tiến độ</th>
            <th>Task cá nhân</th>
            <th>Doing</th>
            <th>Review</th>
            <th>Done</th>
            <th>Quá hạn</th>
            <th>Health</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {projects.map(project => (
            <tr
              key={project.project_id}
              className={selectedProjectId === project.project_id ? 'my-project-row my-project-row--selected' : 'my-project-row'}
              onClick={() => onSelect(project.project_id)}
            >
              <td>
                <strong>{project.project_name}</strong>
                <small>{project.project_code || 'NO-CODE'}</small>
              </td>
              <td>{formatRole(project.project_role)}</td>
              <td>{project.department || 'N/A'}</td>
              <td>{formatDate(project.due_date)}</td>
              <td><ProjectProgress value={project.progress} /></td>
              <td>{project.assigned_tasks}</td>
              <td>{project.doing_tasks}</td>
              <td>{project.review_tasks}</td>
              <td>{project.done_tasks}</td>
              <td className={project.overdue_tasks > 0 ? 'text-danger' : ''}>{project.overdue_tasks}</td>
              <td><HealthBadge health={project.project_health} /></td>
              <td><button type="button" className="button-secondary">Xem task</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MyProjectTaskTable({ tasks }: { tasks: TaskSummary[] }) {
  return (
    <div className="table-wrap">
      <table className="data-table my-project-task-table">
        <thead><tr><th>Task</th><th>Trạng thái</th><th>Deadline</th><th>Ưu tiên</th><th>Weight</th></tr></thead>
        <tbody>
          {tasks.map(task => (
            <tr key={task.id}>
              <td>{task.title}</td>
              <td><span className={`task-status task-status--${task.status}`}>{task.status}</span></td>
              <td className={task.is_overdue ? 'text-danger' : ''}>{formatDate(task.deadline)}</td>
              <td>{task.priority}</td>
              <td>{task.base_weight}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SummaryCard({ label, value, danger = false }: { label: string; value: number; danger?: boolean }) {
  return (
    <div className={danger ? 'my-project-summary-card my-project-summary-card--danger' : 'my-project-summary-card'}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ProjectProgress({ value }: { value: number }) {
  const normalized = Math.max(0, Math.min(100, value));
  return (
    <div className="my-project-progress">
      <div><span style={{ width: `${normalized}%` }} /></div>
      <strong>{Math.round(normalized)}%</strong>
    </div>
  );
}

function HealthBadge({ health }: { health: string }) {
  return <span className={`health-badge health-badge--${health.toLowerCase()}`}>{health}</span>;
}

function formatRole(role: MyProject['project_role']) {
  return role ? role.split('_').join(' ') : 'Manager scope';
}

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleDateString('vi-VN') : 'N/A';
}
