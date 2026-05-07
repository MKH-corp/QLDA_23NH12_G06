import { useState } from 'react';
import { getProjects, createProject } from '../api/services';
import { useFetch } from '../hooks/useApi';
import { DataTable } from '../components/DataTable';

export function ProjectManagementPage() {
  const { data: projects, loading, error, refetch } = useFetch(getProjects);
  const [isModalOpen, setModalOpen] = useState(false);

  // Loading State chuẩn Enterprise
  if (loading) return <div className="screen-center"><div className="loading">Loading projects...</div></div>;
  if (error) return <div className="error-state">Error: {error}</div>;

  return (
    <div className="page-container">
      <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
        <h2>📁 Project Management</h2>
        <button className="btn-gradient" onClick={() => setModalOpen(true)}>+ New Project</button>
      </header>

      {/* Tận dụng lại DataTable cũ, đổ Data thật vào */}
      <div className="glass-panel">
        <DataTable
          title="Active Projects"
          items={projects || []}
          emptyText="No projects found. Create one to get started!"
          columns={[
            { key: 'name', title: 'Project Name', render: (p) => <span style={{ fontWeight: 600 }}>{p.name}</span> },
            { key: 'progress', title: 'Progress', render: (p) => (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '13px', width: '35px' }}>{p.progress}%</span>
                <div className="progress-bar-bg" style={{ width: '100px', height: '6px' }}>
                  <div className="progress-bar-fill" style={{ width: `${p.progress}%` }}></div>
                </div>
              </div>
            )},
            { key: 'tasks', title: 'Total Tasks', render: (p) => p.total_tasks },
            { key: 'status', title: 'Status', render: (p) => <span className={`badge badge--${p.status}`}>{p.status.toUpperCase()}</span> },
          ]}
        />
      </div>
    </div>
  );
}