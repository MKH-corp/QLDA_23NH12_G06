import { useEffect, useState } from 'react';
import { getDashboardData, type DashboardData } from '../api/dashboard';
import { RecentActivityTimeline } from '../components/RecentActivityTimeline';
import { PageHeader, StatCard } from '../components/ui';

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
    return <div className="screen-center"><div className="loading">Đang tải dashboard...</div></div>;
  }

  return (
    <div className="admin-dashboard">
      <PageHeader
        eyebrow="Dashboard quản trị"
        title="Tổng quan hệ thống"
        description="Theo dõi nhanh nhân sự, tiến độ công việc và hiệu suất toàn tổ chức."
      />

      <div className="dashboard-stat-grid">
        <StatCard icon="users" label="Tổng nhân viên" value={data.stats.total_employees} tone="blue" hint="Tài khoản trong hệ thống" />
        <StatCard icon="building" label="Phòng ban hoạt động" value={data.stats.active_departments} tone="green" hint="Đang vận hành" />
        <StatCard icon="check" label="Công việc hoàn thành" value={data.stats.completed_tasks} tone="purple" hint="Tổng số task đã chốt" />
        <StatCard icon="kpi" label="KPI trung bình" value={`${data.stats.avg_kpi}%`} tone="orange" hint="Hiệu suất toàn công ty" />
      </div>

      <div className="dashboard-layout">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">So sánh nội bộ</p>
                <h2 className="panel-title">Hiệu suất theo phòng ban</h2>
              </div>
              <span className="panel-heading__note">Điểm KPI trung bình</span>
            </div>
            <div className="department-chart">
              {data.department_charts.map((dept, i) => (
                <div key={dept.id} className="department-chart__item">
                  <strong>{dept.score}%</strong>
                  <div style={{
                    height: `${dept.score === 0 ? 10 : dept.score}px`,
                    background: i % 2 === 0 ? 'linear-gradient(0deg, #3b82f6, #93c5fd)' : 'linear-gradient(0deg, #8b5cf6, #c4b5fd)',
                  }} />
                  <span>{dept.name}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel">
            <h2 className="panel-title">Nhân viên có hiệu suất cao</h2>
            <table className="modern-table">
              <thead>
                <tr>
                  <th>Nhân viên</th>
                  <th>Phòng ban</th>
                  <th>Đã hoàn thành</th>
                  <th>Điểm KPI</th>
                  <th>Đánh giá</th>
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
                      {user.kpi_score >= 90 ? <span className="badge badge--low">Xuất sắc</span> : <span className="badge badge--medium">Cần cải thiện</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-panel insight-feature">
            <h2 className="panel-title" style={{ color: 'white' }}>Insight hiệu suất</h2>
            <p style={{ fontSize: '14px', lineHeight: '1.6', opacity: 0.9 }}>
              {data.ai_insights}
            </p>
          </div>

          <div className="glass-panel">
            <h2 className="panel-title">Hoạt động gần đây</h2>
            <RecentActivityTimeline />
          </div>
        </div>
      </div>
    </div>
  );
}
