import { useEffect, useState } from 'react';
import { getDashboardData, type DashboardData } from '../api/dashboard';
import { NotificationBell } from '../components/NotificationBell';

export function AdminPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const dashboardData = await getDashboardData();
        setData(dashboardData);
      } catch (err) {
        console.error("Lỗi tải dữ liệu Dashboard:", err);
      } finally {
        setLoading(false);
      }
    };
    void loadData();
  }, []);

  if (loading || !data) {
    return <div className="screen-center"><div className="loading">Initializing Enterprise Dashboard...</div></div>;
  }

  return (
    <div className="admin-dashboard">
      {/* ... GIỮ NGUYÊN PHẦN HEADER & QUICK ACTIONS ... */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1>Admin Dashboard</h1>
        <NotificationBell />
      </div>

      {/* 3. THẺ THỐNG KÊ DATA THẬT */}
      <div className="stats-grid">
        <div className="glass-panel stat-card">
          <div className="stat-icon blue">👥</div>
          <div className="stat-info">
            <p>Total Employees</p>
            <h3>{data.stats.total_employees}</h3>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon green">🏢</div>
          <div className="stat-info">
            <p>Active Departments</p>
            <h3>{data.stats.active_departments}</h3>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon purple">✅</div>
          <div className="stat-info">
            <p>Completed Tasks</p>
            <h3>{data.stats.completed_tasks}</h3>
          </div>
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-icon orange">📈</div>
          <div className="stat-info">
            <p>Avg. KPI Rate</p>
            <h3>{data.stats.avg_kpi}%</h3>
          </div>
        </div>
      </div>

      {/* 4. MAIN LAYOUT GRID */}
      <div className="dashboard-layout">
        
        {/* Bảng nhân viên & Biểu đồ Data Thật */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div className="glass-panel">
            <h2 className="panel-title">📊 Department Performance Analytics</h2>
            <div style={{ height: '200px', display: 'flex', alignItems: 'flex-end', gap: '20px', padding: '20px 0', borderBottom: '1px dashed #e2e8f0' }}>
              {data.department_charts.map((dept, i) => (
                <div key={dept.id} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                  {/* Chiều cao cột = Điểm KPI */}
                  <div style={{ 
                    width: '40px', 
                    height: `${dept.score === 0 ? 10 : dept.score}px`, 
                    background: i % 2 === 0 ? 'linear-gradient(0deg, #3b82f6, #93c5fd)' : 'linear-gradient(0deg, #8b5cf6, #c4b5fd)',
                    borderRadius: '6px 6px 0 0',
                    transition: 'height 1s ease-out'
                  }}></div>
                  <span style={{ fontSize: '12px', color: '#64748b', textAlign: 'center' }}>{dept.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel">
            <h2 className="panel-title">🏆 Top Employee Performance</h2>
            <table className="modern-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Department</th>
                  <th>Tasks Done</th>
                  <th>KPI Score</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.top_performers.map((user) => (
                  <tr key={user.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#3b82f6', color: 'white', display: 'grid', placeItems: 'center', fontWeight: 'bold' }}>
                          {user.full_name.charAt(0)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: '#1e293b' }}>{user.full_name}</div>
                          <div style={{ fontSize: '12px', color: '#64748b' }}>{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td><span className="badge badge--low" style={{ background: '#f1f5f9', color: '#475569' }}>{user.department_name}</span></td>
                    <td style={{ fontWeight: 600 }}>{user.tasks_completed}</td>
                    <td style={{ width: '200px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontWeight: 700, color: user.kpi_score >= 90 ? '#16a34a' : '#ea580c' }}>{user.kpi_score}%</span>
                        <div className="progress-bar-bg">
                          <div className="progress-bar-fill" style={{ width: `${user.kpi_score}%`, background: user.kpi_score >= 90 ? 'linear-gradient(90deg, #22c55e, #86efac)' : 'linear-gradient(90deg, #f59e0b, #fcd34d)' }}></div>
                        </div>
                      </div>
                    </td>
                    <td>
                      {user.kpi_score >= 90 ? <span className="badge badge--low">Excellent</span> : <span className="badge badge--medium">Needs Improvement</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Insights & Hoạt động gần đây */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-panel" style={{ background: 'linear-gradient(135deg, #1e3a8a, #312e81)', color: 'white' }}>
            <h2 className="panel-title" style={{ color: 'white' }}>✨ AI Productivity Insights</h2>
            <p style={{ fontSize: '14px', lineHeight: '1.6', opacity: 0.9 }}>
              {data.ai_insights}
            </p>
          </div>

          <div className="glass-panel">
            <h2 className="panel-title">⏱ Recent Activity</h2>
            <div style={{ marginTop: '20px' }}>
              {data.recent_activities.map((log) => (
                <div key={log.id} className="activity-item">
                  <div className="activity-dot" style={{ background: log.action === 'task' ? '#10b981' : '#3b82f6' }}></div>
                  <div className="activity-content">
                    <h4>{log.action.toUpperCase()} Update</h4>
                    <p>{log.description}</p>
                    <span style={{ fontSize: '11px', color: '#94a3b8' }}>{log.time_ago}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}