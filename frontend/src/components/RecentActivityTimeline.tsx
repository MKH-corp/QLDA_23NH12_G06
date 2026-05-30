import { useEffect, useState } from 'react';
import { getRecentActivities, type ActivityLog } from '../api/activities';
import { PaginationControls } from './PaginationControls';

export function RecentActivityTimeline() {
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);

  const fetchActivities = async () => {
    try {
      const res = await getRecentActivities(page, 5);
      setActivities(res.data);
      setPages(res.pages);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActivities();
    // Realtime nhẹ: Tự động refresh log mỗi 30 giây
    const interval = setInterval(fetchActivities, 30000);
    return () => clearInterval(interval);
  }, [page]);

  // Helper chọn màu Dot tùy theo Action (Đảm bảo SaaS UX)
  const getDotStyle = (actionType: string) => {
    switch (actionType) {
      case 'CREATE': return { background: '#10b981' }; // Green
      case 'DELETE': return { background: '#ef4444' }; // Red
      case 'UPDATE': return { background: '#f59e0b' }; // Orange
      case 'COMPLETE': return { background: '#3b82f6' }; // Blue
      default: return { background: '#94a3b8' };
    }
  };

  if (loading) return <div style={{ padding: '20px', color: '#64748b', fontSize: '13px' }}>Đang tải hoạt động...</div>;
  if (activities.length === 0) return <div style={{ padding: '20px', color: '#64748b', fontSize: '13px' }}>Chưa có hoạt động gần đây.</div>;

  return (
    <div style={{ marginTop: '20px' }}>
      {activities?.map((log) => (
        <div key={log.id} className="activity-item">
          <div className="activity-dot" style={getDotStyle(log.action_type)}></div>
          <div className="activity-content">
            <h4>{log.user_name} 
              <span style={{ fontWeight: 'normal', color: '#64748b', fontSize: '13px', marginLeft: '6px' }}>
                {log.action_type} {log.entity_type}
              </span>
            </h4>
            <p>{log.description}</p>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>{log.time_ago}</span>
          </div>
        </div>
      ))}
      <button 
        className="btn-outline" 
        style={{ width: '100%', marginTop: '16px', justifyContent: 'center' }}
        onClick={fetchActivities}
      >
        Tải lại hoạt động
      </button>
      <PaginationControls page={page} pages={pages} total={total} onPageChange={setPage} />
    </div>
  );
}
