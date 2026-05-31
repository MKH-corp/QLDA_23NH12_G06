import { useEffect, useState } from 'react';

import { getMyProjects } from '../api/projects';
import type { MyProject } from '../types/project';

export function MyProjectsPage() {
  const [projects, setProjects] = useState<MyProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    getMyProjects()
      .then((data) => {
        if (mounted) setProjects(data);
      })
      .catch((err) => {
        if (mounted) setError(err instanceof Error ? err.message : 'Không tải được danh sách dự án');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">My Projects</p>
          <h2>Dự án của tôi</h2>
        </div>
      </div>

      {loading ? <p>Đang tải dự án...</p> : null}
      {error ? <div className="error-box">{error}</div> : null}
      {!loading && !error && projects.length === 0 ? (
        <div className="empty-state">Bạn chưa được phân công vào dự án nào.</div>
      ) : null}

      <div className="project-grid">
        {projects.map((project) => (
          <article key={project.project_id} className="project-card">
            <div className="project-card__header">
              <div>
                <p className="eyebrow">{project.project_code || 'NO-CODE'}</p>
                <h3>{project.project_name}</h3>
              </div>
              <span className={`status-pill status-${project.project_status.toLowerCase()}`}>
                {project.project_status}
              </span>
            </div>
            <p>{project.description || 'Không có mô tả'}</p>
            <div className="project-progress">
              <span>Tiến độ</span>
              <strong>{Math.round(project.progress)}%</strong>
            </div>
            <div className="progress-bar">
              <span style={{ width: `${Math.min(project.progress, 100)}%` }} />
            </div>
            <div className="project-meta">
              <span>Vai trò: {project.project_role || 'N/A'}</span>
              <span>Đóng góp: {project.contribution_share}%</span>
              <span>Deadline: {project.due_date ? new Date(project.due_date).toLocaleDateString('vi-VN') : 'N/A'}</span>
              <span>Health: {project.project_health}</span>
            </div>
            <div className="stats-grid">
              <Stat label="Assigned" value={project.assigned_tasks} />
              <Stat label="Doing" value={project.doing_tasks} />
              <Stat label="Review" value={project.review_tasks} />
              <Stat label="Done" value={project.done_tasks} />
              <Stat label="Overdue" value={project.overdue_tasks} danger={project.overdue_tasks > 0} />
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value, danger = false }: { label: string; value: number; danger?: boolean }) {
  return (
    <div className={danger ? 'stat-card stat-card--danger' : 'stat-card'}>
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}
