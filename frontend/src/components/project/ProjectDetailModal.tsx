import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  addProjectMember,
  completeMilestone,
  createMilestone,
  deleteMilestone,
  getAssignableUsers,
  getProjectTasks,
  projectApi,
  removeMember,
  updateMilestone,
  updateProjectMember,
} from '../../api/projects';
import { getDepartments, getUsers } from '../../api/references';
import { createTask, deleteTask, getTask, updateTask } from '../../api/tasks';
import { useAuth } from '../../context/AuthContext';
import type {
  AssignableUser,
  MemberRole,
  ProjectOverview,
  ProjectReport,
  TaskSummary,
} from '../../types/project';
import type { DepartmentOption, UserOption } from '../../types/reference';
import type { Task, TaskFormValues } from '../../types/task';
import { TaskForm } from '../TaskForm';

interface ProjectDetailModalProps {
  projectId: number;
  onClose: () => void;
}

type DetailTab = 'overview' | 'members' | 'tasks' | 'milestones' | 'reports';

const TERMINAL_STATUSES = ['COMPLETED', 'CANCELLED', 'ARCHIVED'];
const TABS: Array<{ id: DetailTab; label: string }> = [
  { id: 'overview', label: 'Tổng quan' },
  { id: 'members', label: 'Nhân viên' },
  { id: 'tasks', label: 'Task' },
  { id: 'milestones', label: 'Milestone' },
  { id: 'reports', label: 'Báo cáo' },
];

export function ProjectDetailModal({ projectId, onClose }: ProjectDetailModalProps) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<DetailTab>('overview');
  const [project, setProject] = useState<ProjectOverview | null>(null);
  const [report, setReport] = useState<ProjectReport | null>(null);
  const [projectTasks, setProjectTasks] = useState<TaskSummary[]>([]);
  const [assignableUsers, setAssignableUsers] = useState<AssignableUser[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showTaskForm, setShowTaskForm] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [taskSearch, setTaskSearch] = useState('');
  const [taskStatus, setTaskStatus] = useState('');
  const [taskAssignee, setTaskAssignee] = useState('');
  const [onlyOverdue, setOnlyOverdue] = useState(false);

  const [memberUserId, setMemberUserId] = useState('');
  const [memberRole, setMemberRole] = useState<MemberRole>('MEMBER');
  const [milestoneTitle, setMilestoneTitle] = useState('');
  const [milestoneDueDate, setMilestoneDueDate] = useState('');
  const [milestoneWeight, setMilestoneWeight] = useState(1);

  const reloadProject = useCallback(async () => {
    const [projectData, taskData, assignableData, reportData] = await Promise.all([
      projectApi.getById(projectId),
      getProjectTasks(projectId),
      getAssignableUsers(projectId),
      projectApi.getReport(projectId),
    ]);
    setProject(projectData);
    setProjectTasks(taskData);
    setAssignableUsers(assignableData);
    setReport(reportData);
  }, [projectId]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    reloadProject()
      .catch((reason: Error) => setError(reason.message || 'Không tải được project'))
      .finally(() => setLoading(false));
  }, [reloadProject]);

  useEffect(() => {
    Promise.all([getUsers(), getDepartments()])
      .then(([userData, departmentData]) => {
        setUsers(userData);
        setDepartments(departmentData);
      })
      .catch(() => {
        setUsers([]);
        setDepartments([]);
      });
  }, []);

  const runAction = async (action: () => Promise<void>) => {
    setError(null);
    try {
      await action();
    } catch (reason: any) {
      setError(reason.message || 'Không thực hiện được thao tác');
    }
  };

  const canManage = user?.role === 'admin' || user?.role === 'manager';
  const canEditContent = canManage && project != null && !TERMINAL_STATUSES.includes(project.status);
  const analytics = report?.analytics ?? project?.analytics;
  const contributionTotal = project?.members
    .filter(member => member.is_active)
    .reduce((sum, member) => sum + member.contribution_share, 0) ?? 0;
  const memberPerformance = new Map(
    (report?.member_performance ?? []).map(item => [item.user_id, item]),
  );
  const candidateUsers = users.filter(candidate =>
    candidate.is_active
    && candidate.department_id === project?.department_id
    && !project?.members.some(member => member.user_id === candidate.id && member.is_active),
  );
  const filteredTasks = useMemo(() => projectTasks.filter(task =>
    task.title.toLowerCase().includes(taskSearch.toLowerCase())
    && (!taskStatus || task.status === taskStatus)
    && (!taskAssignee || task.assignee_id === Number(taskAssignee))
    && (!onlyOverdue || task.is_overdue),
  ), [onlyOverdue, projectTasks, taskAssignee, taskSearch, taskStatus]);

  const handleSaveTask = async (values: TaskFormValues) => {
    await runAction(async () => {
      const payload = { ...values, project_id: projectId };
      if (editingTask) {
        await updateTask(editingTask.id, payload);
      } else {
        await createTask(payload);
      }
      setEditingTask(null);
      setShowTaskForm(false);
      await reloadProject();
    });
  };

  const handleEditTask = async (taskId: number) => {
    await runAction(async () => {
      setEditingTask(await getTask(taskId));
      setShowTaskForm(true);
    });
  };

  const handleDeleteTask = async (taskId: number) => {
    if (!confirm('Xóa task này?')) return;
    await runAction(async () => {
      await deleteTask(taskId);
      await reloadProject();
    });
  };

  const handleAddMember = async () => {
    if (!memberUserId) return;
    await runAction(async () => {
      await addProjectMember(projectId, {
        user_id: Number(memberUserId),
        role: memberRole,
        is_active: true,
      });
      setMemberUserId('');
      await reloadProject();
    });
  };

  const handleUpdateMember = async (
    userId: number,
    payload: { role?: MemberRole; contribution_share?: number; is_active?: boolean },
  ) => {
    await runAction(async () => {
      await updateProjectMember(projectId, userId, payload);
      await reloadProject();
    });
  };

  const handleCreateMilestone = async () => {
    if (!milestoneTitle.trim()) return;
    await runAction(async () => {
      await createMilestone(projectId, {
        title: milestoneTitle.trim(),
        due_date: milestoneDueDate || undefined,
        weight: milestoneWeight,
      });
      setMilestoneTitle('');
      setMilestoneDueDate('');
      setMilestoneWeight(1);
      await reloadProject();
    });
  };

  const handleRenameMilestone = async (milestoneId: number, currentTitle: string) => {
    const title = prompt('Tên milestone', currentTitle)?.trim();
    if (!title || title === currentTitle) return;
    await runAction(async () => {
      await updateMilestone(projectId, milestoneId, { title });
      await reloadProject();
    });
  };

  return (
    <div className="project-modal-backdrop" onClick={onClose}>
      <div className="project-detail-modal" onClick={event => event.stopPropagation()}>
        <header className="project-detail-header">
          <div>
            <div className="project-code">{project?.code || 'PROJECT'}</div>
            <h2>{project?.name || 'Chi tiết dự án'}</h2>
          </div>
          <button type="button" className="btn-outline" onClick={onClose}>Đóng</button>
        </header>

        {error ? <div className="alert alert--error">{error}</div> : null}
        {loading ? <div className="project-empty">Đang tải dữ liệu...</div> : null}

        {!loading && project ? (
          <>
            <nav className="project-tabs">
              {TABS.map(tab => (
                <button
                  key={tab.id}
                  type="button"
                  className={activeTab === tab.id ? 'project-tab project-tab--active' : 'project-tab'}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.label}
                </button>
              ))}
            </nav>

            {activeTab === 'overview' ? (
              <section className="project-tab-content">
                <div className="project-metric-grid">
                  <Metric label="Trạng thái" value={project.status} />
                  <Metric label="Ưu tiên" value={project.priority} />
                  <Metric label="Tiến độ tổng" value={`${analytics?.project_progress_percentage ?? 0}%`} />
                  <Metric label="Task hoàn thành" value={`${analytics?.done_tasks ?? 0}/${analytics?.total_tasks ?? 0}`} />
                  <Metric label="Task quá hạn" value={analytics?.overdue_tasks ?? 0} />
                  <Metric label="Task blocked" value={analytics?.blocked_tasks ?? 0} />
                  <Metric label="Thành viên" value={analytics?.total_members ?? project.members.length} />
                  <Metric label="Milestone" value={`${analytics?.completed_milestones ?? 0}/${analytics?.total_milestones ?? 0}`} />
                </div>
                <Progress label="Tiến độ tổng" value={analytics?.project_progress_percentage ?? 0} />
                <Progress label="Hoàn thành task" value={analytics?.task_completion_percentage ?? 0} />
                <Progress label="Hoàn thành milestone" value={analytics?.milestone_completion_percentage ?? 0} />
                <div className="project-overview-grid">
                  <div><strong>Phòng ban</strong><span>{project.department_name || 'Chưa gán'}</span></div>
                  <div><strong>Manager</strong><span>{project.manager_name || 'Chưa gán'}</span></div>
                  <div><strong>Bắt đầu</strong><span>{formatDate(project.start_date)}</span></div>
                  <div><strong>Kết thúc</strong><span>{formatDate(project.end_date)}</span></div>
                  <div><strong>Giờ dự kiến</strong><span>{analytics?.estimated_hours ?? 0}</span></div>
                  <div><strong>Giờ thực tế</strong><span>{analytics?.actual_hours ?? 0}</span></div>
                  <div><strong>Ngân sách</strong><span>{project.estimated_budget ?? 'Chưa khai báo'}</span></div>
                  <div><strong>Project weight</strong><span>{project.project_weight}</span></div>
                </div>
                <p className="project-description">{project.description || 'Chưa có mô tả.'}</p>
              </section>
            ) : null}

            {activeTab === 'members' ? (
              <section className="project-tab-content">
                <div className="project-section-heading">
                  <h3>Nhân viên trong dự án</h3>
                  <strong className={contributionTotal === 100 ? 'text-success' : 'text-warning'}>
                    Contribution: {contributionTotal}%
                  </strong>
                </div>
                {canEditContent ? (
                  <div className="project-inline-form">
                    <select value={memberUserId} onChange={event => setMemberUserId(event.target.value)}>
                      <option value="">Chọn nhân sự</option>
                      {candidateUsers.map(candidate => (
                        <option key={candidate.id} value={candidate.id}>{candidate.full_name}</option>
                      ))}
                    </select>
                    <select value={memberRole} onChange={event => setMemberRole(event.target.value as MemberRole)}>
                      {['PROJECT_MANAGER', 'TEAM_LEAD', 'MEMBER', 'VIEWER'].map(role => (
                        <option key={role} value={role}>{role}</option>
                      ))}
                    </select>
                    <button type="button" className="btn-primary" onClick={() => void handleAddMember()}>Thêm</button>
                  </div>
                ) : null}
                <div className="project-table-wrap">
                  <table className="project-table">
                    <thead><tr><th>Nhân viên</th><th>Phòng ban</th><th>Vai trò</th><th>Task</th><th>Done</th><th>Contribution</th><th>Thao tác</th></tr></thead>
                    <tbody>{project.members.map(member => {
                      const performance = memberPerformance.get(member.user_id);
                      return (
                        <tr key={member.user_id}>
                          <td><strong>{member.full_name}</strong><small>{member.email}</small></td>
                          <td>{performance?.department_name || project.department_name}</td>
                          <td>{canEditContent && member.is_active ? (
                            <select value={member.role} onChange={event => void handleUpdateMember(member.user_id, { role: event.target.value as MemberRole })}>
                              {['PROJECT_MANAGER', 'TEAM_LEAD', 'MEMBER', 'VIEWER'].map(role => <option key={role}>{role}</option>)}
                            </select>
                          ) : member.role}</td>
                          <td>{performance?.total_tasks ?? 0}</td>
                          <td>{performance?.done_tasks ?? 0}</td>
                          <td>{canEditContent && member.is_active ? (
                            <input
                              type="number"
                              min={0}
                              max={100}
                              defaultValue={member.contribution_share}
                              onBlur={event => void handleUpdateMember(member.user_id, { contribution_share: Number(event.target.value) })}
                            />
                          ) : `${member.contribution_share}%`}</td>
                          <td>{canEditContent && member.is_active ? (
                            <button type="button" className="btn-outline" onClick={() => void runAction(async () => {
                              await removeMember(projectId, member.user_id);
                              await reloadProject();
                            })}>Deactivate</button>
                          ) : member.is_active ? 'Active' : 'Inactive'}</td>
                        </tr>
                      );
                    })}</tbody>
                  </table>
                </div>
              </section>
            ) : null}

            {activeTab === 'tasks' ? (
              <section className="project-tab-content">
                <div className="project-section-heading">
                  <h3>Task của project</h3>
                  {canEditContent ? <button type="button" className="btn-gradient" onClick={() => {
                    setEditingTask(null);
                    setShowTaskForm(open => !open);
                  }}>+ Giao task</button> : null}
                </div>
                {showTaskForm ? (
                  <TaskForm
                    mode={editingTask ? 'edit' : 'create'}
                    task={editingTask}
                    departments={departments.filter(department => department.id === project.department_id)}
                    users={[]}
                    projectMembers={assignableUsers}
                    referencesLoading={loading}
                    fixedProjectId={projectId}
                    hideProject
                    hideDepartment
                    onSubmit={handleSaveTask}
                    onCancel={() => {
                      setEditingTask(null);
                      setShowTaskForm(false);
                    }}
                  />
                ) : null}
                <div className="project-filter-row">
                  <input placeholder="Tìm task" value={taskSearch} onChange={event => setTaskSearch(event.target.value)} />
                  <select value={taskStatus} onChange={event => setTaskStatus(event.target.value)}>
                    <option value="">Tất cả trạng thái</option>
                    {['todo', 'doing', 'in_review', 'blocked', 'done'].map(status => <option key={status}>{status}</option>)}
                  </select>
                  <select value={taskAssignee} onChange={event => setTaskAssignee(event.target.value)}>
                    <option value="">Tất cả nhân sự</option>
                    {assignableUsers.map(member => <option key={member.id} value={member.id}>{member.full_name}</option>)}
                  </select>
                  <label><input type="checkbox" checked={onlyOverdue} onChange={event => setOnlyOverdue(event.target.checked)} /> Quá hạn</label>
                </div>
                <div className="project-table-wrap">
                  <table className="project-table">
                    <thead><tr><th>Task</th><th>Assignee</th><th>Trạng thái</th><th>Deadline</th><th>Weight</th><th>Thao tác</th></tr></thead>
                    <tbody>{filteredTasks.map(task => (
                      <tr key={task.id}>
                        <td>{task.title}</td><td>{task.assignee_name}</td><td>{task.status}</td>
                        <td className={task.is_overdue ? 'text-danger' : ''}>{formatDate(task.deadline)}</td>
                        <td>{task.base_weight}</td>
                        <td>{canEditContent ? (
                          <div className="project-actions">
                            <button type="button" className="btn-outline" onClick={() => void handleEditTask(task.id)}>Sửa</button>
                            <button type="button" className="btn-outline" onClick={() => void handleDeleteTask(task.id)}>Xóa</button>
                          </div>
                        ) : 'Xem'}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                  {filteredTasks.length === 0 ? <div className="project-empty">Không có task phù hợp.</div> : null}
                </div>
              </section>
            ) : null}

            {activeTab === 'milestones' ? (
              <section className="project-tab-content">
                <h3>Milestone</h3>
                {canEditContent ? (
                  <div className="project-inline-form">
                    <input placeholder="Tên milestone" value={milestoneTitle} onChange={event => setMilestoneTitle(event.target.value)} />
                    <input type="date" value={milestoneDueDate} onChange={event => setMilestoneDueDate(event.target.value)} />
                    <input type="number" min={1} max={10} value={milestoneWeight} onChange={event => setMilestoneWeight(Number(event.target.value))} />
                    <button type="button" className="btn-primary" onClick={() => void handleCreateMilestone()}>Thêm</button>
                  </div>
                ) : null}
                <div className="project-table-wrap">
                  <table className="project-table">
                    <thead><tr><th>Milestone</th><th>Deadline</th><th>Weight</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
                    <tbody>{project.milestones.map(milestone => (
                      <tr key={milestone.id}>
                        <td>{milestone.title}</td><td>{formatDate(milestone.due_date)}</td><td>{milestone.weight}</td>
                        <td>{milestone.is_completed ? 'Done' : 'Open'}</td>
                        <td><div className="project-actions">
                          {canEditContent && !milestone.is_completed ? <button type="button" className="btn-outline" onClick={() => void runAction(async () => {
                            await completeMilestone(projectId, milestone.id);
                            await reloadProject();
                          })}>Hoàn thành</button> : null}
                          {canEditContent ? <button type="button" className="btn-outline" onClick={() => void handleRenameMilestone(milestone.id, milestone.title)}>Sửa</button> : null}
                          {canEditContent ? <button type="button" className="btn-outline" onClick={() => void runAction(async () => {
                            if (!confirm('Xóa milestone này?')) return;
                            await deleteMilestone(projectId, milestone.id);
                            await reloadProject();
                          })}>Xóa</button> : null}
                        </div></td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              </section>
            ) : null}

            {activeTab === 'reports' ? (
              <section className="project-tab-content">
                <div className="project-metric-grid">
                  <Metric label="Tổng task" value={analytics?.total_tasks ?? 0} />
                  <Metric label="Done" value={analytics?.done_tasks ?? 0} />
                  <Metric label="Doing" value={analytics?.doing_tasks ?? 0} />
                  <Metric label="Blocked" value={analytics?.blocked_tasks ?? 0} />
                  <Metric label="Quá hạn" value={analytics?.overdue_tasks ?? 0} />
                  <Metric label="Risk" value={analytics?.risk_level ?? 'LOW'} />
                </div>
                <div className="project-overview-grid">
                  <div><strong>Đóng góp cao nhất</strong><span>{report?.top_contributor?.full_name || 'Chưa có dữ liệu'}</span></div>
                  <div><strong>Nhiều task quá hạn nhất</strong><span>{report?.most_overdue_member?.full_name || 'Không có task quá hạn'}</span></div>
                </div>
                <h3>Phân bố trạng thái task</h3>
                {Object.entries(report?.task_status_breakdown ?? {}).map(([label, value]) => (
                  <Progress key={label} label={`${label}: ${value}`} value={(analytics?.total_tasks ?? 0) ? value / (analytics?.total_tasks ?? 1) * 100 : 0} />
                ))}
                <h3>Hiệu suất theo nhân viên</h3>
                <div className="project-table-wrap">
                  <table className="project-table">
                    <thead><tr><th>Nhân viên</th><th>Vai trò</th><th>Task</th><th>Done</th><th>Quá hạn</th><th>Tỷ lệ</th><th>KPI</th></tr></thead>
                    <tbody>{report?.member_performance.map(member => (
                      <tr key={member.user_id}>
                        <td>{member.full_name}</td><td>{member.project_role}</td><td>{member.total_tasks}</td>
                        <td>{member.done_tasks}</td><td>{member.overdue_tasks}</td>
                        <td>{member.task_completion_percentage}%</td><td>{member.kpi_score}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              </section>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return <div className="project-metric"><small>{label}</small><strong>{value}</strong></div>;
}

function Progress({ label, value }: { label: string; value: number }) {
  const normalized = Math.max(0, Math.min(100, value));
  return (
    <div className="project-progress">
      <div><span>{label}</span><strong>{Math.round(normalized)}%</strong></div>
      <div className="project-progress-track"><span style={{ width: `${normalized}%` }} /></div>
    </div>
  );
}

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleDateString('vi-VN') : 'N/A';
}
