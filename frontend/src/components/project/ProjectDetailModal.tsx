import { useState, useEffect } from 'react';
import { addProjectMember, projectApi, removeMember, updateProjectMember } from '../../api/projects';
import { getUsers } from '../../api/references';
import { MemberRole, ProjectOverview } from '../../types/project';
import type { UserOption } from '../../types/reference';

interface ProjectDetailModalProps {
  projectId: number;
  onClose: () => void;
}

export function ProjectDetailModal({ projectId, onClose }: ProjectDetailModalProps) {
  const [project, setProject] = useState<ProjectOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [memberUserId, setMemberUserId] = useState('');
  const [memberRole, setMemberRole] = useState<MemberRole>('MEMBER');
  const [memberShare, setMemberShare] = useState(0);
  const [memberError, setMemberError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await projectApi.getById(projectId);
        setProject(data);
      } catch (e: any) {
        setError(e.message || 'Lỗi tải dữ liệu');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [projectId]);

  useEffect(() => {
    getUsers().then(setUsers).catch(() => setUsers([]));
  }, []);

  const memberCount = project?.members.length ?? 0;
  const totalTasks = project?.analytics?.total_tasks ?? project?.recent_tasks.length ?? 0;
  const completedTasks = project?.analytics?.completed_tasks ?? 0;
  const overdueTasks = project?.analytics?.overdue_tasks ?? 0;
  const milestoneCount = project?.milestones.length ?? 0;
  const milestonesDone = project?.milestones.filter((milestone) => milestone.is_completed).length ?? 0;
  const contributionTotal = project?.members
    .filter((member) => member.is_active)
    .reduce((sum, member) => sum + member.contribution_share, 0) ?? 0;

  const reloadProject = async () => {
    const data = await projectApi.getById(projectId);
    setProject(data);
  };

  const handleAddMember = async () => {
    if (!memberUserId) return;
    try {
      setMemberError(null);
      await addProjectMember(projectId, {
        user_id: Number(memberUserId),
        role: memberRole,
        contribution_share: memberShare,
        is_active: true,
      });
      setMemberUserId('');
      setMemberShare(0);
      await reloadProject();
    } catch (e: any) {
      setMemberError(e.message || 'Không thêm được thành viên');
    }
  };

  const handleUpdateMember = async (userId: number, role: MemberRole, share: number, isActive: boolean) => {
    try {
      setMemberError(null);
      await updateProjectMember(projectId, userId, { role, contribution_share: share, is_active: isActive });
      await reloadProject();
    } catch (e: any) {
      setMemberError(e.message || 'Không cập nhật được thành viên');
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'white',
          borderRadius: 12,
          width: '90%',
          maxWidth: 700,
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: '0 20px 60px rgba(0,0,0,.3)',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ margin: 0, color: '#1e3a8a' }}>📋 Chi tiết Dự án</h2>
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                fontSize: 24,
                cursor: 'pointer',
              }}
            >
              ✕
            </button>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b' }}>
              Đang tải...
            </div>
          ) : error ? (
            <div style={{ background: '#fee2e2', color: '#991b1b', padding: 12, borderRadius: 8 }}>
              ❌ {error}
            </div>
          ) : project ? (
            <div style={{ display: 'grid', gap: 20 }}>
              {/* Header */}
              <div style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: 16 }}>
                <div style={{ fontSize: 11, color: '#94a3b8', fontWeight: 600, marginBottom: 4 }}>
                  {project.code || '—'}
                </div>
                <h3 style={{ margin: '0 0 8px', fontSize: 20, color: '#0f172a' }}>
                  {project.name}
                </h3>
                <p style={{ margin: 0, color: '#64748b' }}>{project.description || '(Không có mô tả)'}</p>
              </div>

              {/* Stats */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
                {[
                  { label: 'Trạng thái', value: project.status },
                  { label: 'Ưu tiên', value: project.priority },
                  { label: 'Phòng ban', value: project.department_name || '—' },
                  { label: 'Quản lý', value: project.manager_name || '—' },
                  { label: 'Tiến độ', value: `${Math.round(project.progress_percentage)}%` },
                  { label: 'Nhân sự', value: `${memberCount} người` },
                ].map(stat => (
                  <div key={stat.label} style={{ background: '#f8fafc', padding: 12, borderRadius: 8 }}>
                    <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>{stat.label}</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#0f172a' }}>{stat.value}</div>
                  </div>
                ))}
              </div>

              {/* Dates */}
              <div style={{ background: '#f8fafc', padding: 12, borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>📅 Thời gian</div>
                <div style={{ display: 'grid', gap: 4 }}>
                  <div>
                    <span style={{ color: '#64748b' }}>Bắt đầu:</span>{' '}
                    <span style={{ fontWeight: 600 }}>
                      {project.start_date 
                        ? new Date(project.start_date).toLocaleDateString('vi-VN')
                        : '—'
                      }
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Kết thúc:</span>{' '}
                    <span style={{ fontWeight: 600 }}>
                      {project.end_date
                        ? new Date(project.end_date).toLocaleDateString('vi-VN')
                        : '—'
                      }
                    </span>
                  </div>
                </div>
              </div>

              {/* Tasks */}
              <div>
                <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>✅ Công việc</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                  {[
                    { label: 'Tổng', value: totalTasks },
                    { label: 'Hoàn thành', value: completedTasks },
                    { label: 'Quá hạn', value: overdueTasks },
                  ].map(item => (
                    <div key={item.label} style={{ background: '#f8fafc', padding: 10, borderRadius: 8, textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: '#64748b' }}>{item.label}</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: '#0f172a' }}>{item.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Milestones */}
              <div>
                <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>🎯 Milestone</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                  {[
                    { label: 'Tổng', value: milestoneCount },
                    { label: 'Hoàn thành', value: milestonesDone },
                  ].map(item => (
                    <div key={item.label} style={{ background: '#f8fafc', padding: 10, borderRadius: 8, textAlign: 'center' }}>
                      <div style={{ fontSize: 11, color: '#64748b' }}>{item.label}</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: '#0f172a' }}>{item.value}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ fontSize: 12, color: '#64748b' }}>Members</div>
                  <strong style={{ color: contributionTotal > 100 ? '#dc2626' : contributionTotal === 100 ? '#16a34a' : '#ca8a04' }}>
                    Contribution: {contributionTotal}%
                  </strong>
                </div>
                {memberError ? <div style={{ background: '#fee2e2', color: '#991b1b', padding: 8, borderRadius: 8, marginBottom: 8 }}>{memberError}</div> : null}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 150px 90px auto', gap: 8, marginBottom: 12 }}>
                  <select value={memberUserId} onChange={(event) => setMemberUserId(event.target.value)}>
                    <option value="">Chọn nhân sự</option>
                    {users.map((user) => (
                      <option key={user.id} value={user.id}>{user.full_name}</option>
                    ))}
                  </select>
                  <select value={memberRole} onChange={(event) => setMemberRole(event.target.value as MemberRole)}>
                    <option value="PROJECT_MANAGER">Project Manager</option>
                    <option value="TEAM_LEAD">Tech Lead</option>
                    <option value="MEMBER">Member</option>
                    <option value="VIEWER">Viewer</option>
                  </select>
                  <input type="number" min={0} max={100} value={memberShare} onChange={(event) => setMemberShare(Number(event.target.value))} placeholder="%" />
                  <button type="button" className="btn-primary" onClick={handleAddMember}>Thêm</button>
                </div>
                <div style={{ display: 'grid', gap: 8 }}>
                  {project.members.map((member) => (
                    <div key={member.user_id} style={{ display: 'grid', gridTemplateColumns: '1fr 150px 90px auto', gap: 8, alignItems: 'center', background: '#f8fafc', padding: 10, borderRadius: 8, opacity: member.is_active ? 1 : 0.55 }}>
                      <div>
                        <strong>{member.full_name}</strong>
                        <div style={{ color: '#64748b', fontSize: 12 }}>{member.email}</div>
                      </div>
                      <select value={member.role} onChange={(event) => handleUpdateMember(member.user_id, event.target.value as MemberRole, member.contribution_share, member.is_active)}>
                        <option value="PROJECT_MANAGER">Project Manager</option>
                        <option value="TEAM_LEAD">Tech Lead</option>
                        <option value="MEMBER">Member</option>
                        <option value="VIEWER">Viewer</option>
                      </select>
                      <input type="number" min={0} max={100} defaultValue={member.contribution_share} onBlur={(event) => handleUpdateMember(member.user_id, member.role, Number(event.target.value), member.is_active)} />
                      <button type="button" className="btn-outline" onClick={() => removeMember(projectId, member.user_id).then(reloadProject).catch((e: any) => setMemberError(e.message || 'Không xóa được thành viên'))}>
                        Deactivate
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Close button */}
              <button
                onClick={onClose}
                className="btn-outline"
                style={{ width: '100%', marginTop: 12 }}
              >
                Đóng
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

