import { getProductivityReport } from '../api/services';
import { useFetch } from '../hooks/useApi';

export function ReportsPage() {
  const { data: reportData, loading, error } = useFetch(getProductivityReport);

  if (loading) return <div className="screen-center"><div className="loading">Generating Reports...</div></div>;
  if (error) return <div className="error-state">Error: {error}</div>;

  return (
    <div className="page-container">
      <header style={{ marginBottom: '24px' }}>
        <h2 style={{ color: '#1e3a8a' }}>📈 Productivity Reports</h2>
        <p style={{ color: '#64748b' }}>Department level analytics and task tracking</p>
      </header>

      <div className="dashboard-layout">
        <div className="glass-panel" style={{ flex: 2 }}>
          <h2 className="panel-title">Department Productivity Comparison</h2>
          <table className="modern-table">
            <thead>
              <tr>
                <th>Department</th>
                <th>Total Tasks</th>
                <th>Completed</th>
                <th>Overdue</th>
                <th>Productivity Score</th>
              </tr>
            </thead>
            <tbody>
              {reportData?.map((row, idx) => (
                <tr key={idx}>
                  <td style={{ fontWeight: 600 }}>{row.department_name}</td>
                  <td>{row.total_tasks}</td>
                  <td style={{ color: '#10b981', fontWeight: 'bold' }}>{row.completed}</td>
                  <td style={{ color: '#ef4444' }}>{row.overdue}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontWeight: 700 }}>{row.productivity_score}%</span>
                      <div className="progress-bar-bg" style={{ width: '80px' }}>
                        <div className="progress-bar-fill" style={{ width: `${row.productivity_score}%`, background: row.productivity_score >= 80 ? '#10b981' : '#f59e0b' }}></div>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="glass-panel" style={{ flex: 1, background: 'linear-gradient(135deg, #0f172a, #1e293b)', color: 'white' }}>
          <h2 className="panel-title" style={{ color: 'white' }}>💡 Insights</h2>
          <div style={{ marginTop: '20px', lineHeight: '1.6', fontSize: '14px', color: '#cbd5e1' }}>
            <p><strong>Top Performer:</strong> {reportData?.[0]?.department_name} is leading with a {reportData?.[0]?.productivity_score}% completion rate.</p>
            <hr style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '16px 0' }}/>
            <p><strong>Attention Needed:</strong> Ensure teams with high overdue tasks re-evaluate their current sprint workload.</p>
          </div>
        </div>
      </div>
    </div>
  );
}