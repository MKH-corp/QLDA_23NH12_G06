import { useState, useEffect } from 'react';
import { useFetch } from '../hooks/useApi';
import { getTeamRanking, getUserKpi, type KpiSnapshot } from '../api/kpi';
import { DataTable } from '../components/DataTable';

export function KpiTrackingPage() {
  const { data: teamRanking, loading: rankingLoading } = useFetch(getTeamRanking);
  
  // State quản lý việc chọn Nhân viên để soi điểm
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedUserName, setSelectedUserName] = useState<string>("...");
  const [detailData, setDetailData] = useState<KpiSnapshot | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Gọi API lấy điểm chi tiết mỗi khi Admin click chọn user khác
  useEffect(() => {
    if (selectedUserId) {
      setDetailLoading(true);
      getUserKpi(selectedUserId)
        .then(data => setDetailData(data))
        .catch(err => console.error(err))
        .finally(() => setDetailLoading(false));
    }
  }, [selectedUserId]);

  if (rankingLoading) return <div className="screen-center"><div className="loading">Đang tải KPI...</div></div>;

  const baseScore = detailData?.breakdown?.base_score || 0;
  const onTimeBonus = detailData?.breakdown?.on_time_bonus || 0;
  const overduePenalty = detailData?.breakdown?.overdue_penalty_amount || 0;
  const reopenPenalty = detailData?.breakdown?.reopen_penalty_amount || 0;

  return (
    <div className="page-container">
      <header style={{ marginBottom: '24px' }}>
        <h2 style={{ color: '#1e3a8a' }}>Hiệu suất nhân sự</h2>
        <p style={{ color: '#64748b' }}>Chọn nhân viên để xem chi tiết cách tính KPI.</p>
      </header>

      <div className="dashboard-layout">
        
        {/* BẢNG XẾP HẠNG TOÀN CÔNG TY (BÊN TRÁI) */}
        <div className="glass-panel" style={{ flex: 2 }}>
          <DataTable
            title="Bảng xếp hạng"
            items={teamRanking || []}
            emptyText="Chưa có dữ liệu xếp hạng."
            columns={[
              { 
                key: 'rank', title: 'Hạng',
                render: (u) => {
                  const idx = teamRanking ? teamRanking.indexOf(u) : 0;
                  return <strong style={{ color: idx < 3 ? '#f59e0b' : '#64748b' }}>#{idx + 1}</strong>
                }
              },
              { key: 'name', title: 'Nhân viên', render: (u) => <span style={{ fontWeight: 600 }}>{u.full_name}</span> },
              { key: 'dept', title: 'Phòng ban', render: (u) => <span className="badge badge--low">{u.department_name}</span> },
              { key: 'score', title: 'Điểm', render: (u) => <strong style={{ color: '#10b981' }}>{u.total_score} điểm</strong> },
              { key: 'action', title: 'Chi tiết', render: (u) => (
                <button 
                  className="btn-outline" 
                  style={{ padding: '4px 10px', fontSize: '12px' }}
                  onClick={() => {
                    setSelectedUserId(u.user_id);
                    setSelectedUserName(u.full_name);
                  }}
                >
                  Xem chi tiết
                </button>
              )}
            ]}
          />
        </div>

        {/* BẢNG CHI TIẾT ĐIỂM (BÊN PHẢI) */}
        <div className="glass-panel" style={{ flex: 1, minHeight: '400px' }}>
          <h2 className="panel-title">Chi tiết cách tính</h2>
          
          {!selectedUserId ? (
            <div style={{ display: 'flex', height: '80%', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: '14px', textAlign: 'center' }}>
              Chọn một nhân viên để phân tích hiệu suất.
            </div>
          ) : detailLoading ? (
            <div className="loading" style={{ marginTop: '50px', textAlign: 'center' }}>Đang tải dữ liệu...</div>
          ) : (
            <>
              <h4 style={{ textAlign: 'center', color: '#64748b', marginTop: '10px' }}>Nhân viên: <span style={{ color: '#0f172a' }}>{selectedUserName}</span></h4>
              <div style={{ fontSize: '48px', fontWeight: 800, color: '#10b981', textAlign: 'center', margin: '10px 0' }}>
                {detailData?.total_score || 0} <span style={{ fontSize: '20px', color: '#64748b' }}>điểm</span>
              </div>
              
              <ul style={{ listStyle: 'none', padding: 0, margin: '20px 0 0 0', fontSize: '14px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <li style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
                  <span>Điểm hoàn thành ({detailData?.tasks_completed || 0})</span>
                  <strong style={{ color: '#1e3a8a' }}>+{baseScore.toFixed(1)}</strong>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
                  <span>Thưởng đúng hạn</span>
                  <strong style={{ color: '#10b981' }}>+{onTimeBonus.toFixed(1)}</strong>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
                  <span>Phạt quá hạn ({detailData?.tasks_overdue || 0})</span>
                  <strong style={{ color: '#ef4444' }}>{overduePenalty.toFixed(1)}</strong>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '8px' }}>
                  <span>Phạt mở lại</span>
                  <strong style={{ color: '#ef4444' }}>{reopenPenalty.toFixed(1)}</strong>
                </li>
              </ul>
              
              <p style={{ fontSize: '11px', color: '#94a3b8', textAlign: 'center', marginTop: '30px' }}>
                Snapshot gần nhất: {detailData?.updated_at ? new Date(detailData.updated_at).toLocaleString() : 'Chưa có'}
              </p>
            </>
          )}
        </div>

      </div>
    </div>
  );
}
