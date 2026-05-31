import { useEffect, useMemo, useState } from 'react';

import { getDepartments, getUsers } from '../api/references';
import { createTask, deleteTask, getTasks, updateTask, updateTaskStatus } from '../api/tasks';
import { getAssignableUsers, getProjects } from '../api/projects';
import { Board } from '../components/Board';
import { TaskForm } from '../components/TaskForm';
import { PaginationControls } from '../components/PaginationControls';
import type { DepartmentOption, UserOption } from '../types/reference';
import type { Task, TaskFormValues } from '../types/task';
import type { AssignableUser, ProjectListItem } from '../types/project';
import { useAuth } from '../context/AuthContext';
import { Icon, PageHeader, StatCard } from '../components/ui';

export function ManagerTasksPage() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [projectMembers, setProjectMembers] = useState<AssignableUser[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [loading, setLoading] = useState(true);
  const [referencesLoading, setReferencesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [assigneeFilter, setAssigneeFilter] = useState<string>('all');
  const [overdueFilter, setOverdueFilter] = useState<'all' | 'true'>('all');
  const [projectFilter, setProjectFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);

  const loadReferences = async () => {
    setReferencesLoading(true);
    try {
      const [departmentData, userData, projectData] = await Promise.all([getDepartments(), getUsers(), getProjects()]);
      setDepartments(departmentData);
      setUsers(userData);
      setProjects(projectData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể tải dữ liệu tham chiếu');
    } finally {
      setReferencesLoading(false);
    }
  };

  const loadTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTasks({
        status: statusFilter === 'all' ? undefined : statusFilter,
        overdue: overdueFilter === 'true' ? true : undefined,
        assigneeId: assigneeFilter === 'all' ? undefined : Number(assigneeFilter),
        projectId: projectFilter === 'all' ? undefined : Number(projectFilter),
        page,
      });
      setTasks(data.items);
      setPages(data.pages);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể tải công việc');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadReferences();
  }, []);

  useEffect(() => {
    void loadTasks();
  }, [statusFilter, assigneeFilter, overdueFilter, projectFilter, page]);

  const handleProjectChange = async (projectId: number | null) => {
    try {
      setProjectMembers(projectId ? await getAssignableUsers(projectId) : []);
    } catch (err) {
      setProjectMembers([]);
      setError(err instanceof Error ? err.message : 'Không tải được thành viên project');
    }
  };

  const visibleUsers = useMemo(() => users.filter((item) => item.department_id === user?.department_id), [users, user?.department_id]);
  const taskSummary = useMemo(() => ({
    blocked: tasks.filter(task => task.status === 'blocked').length,
    done: tasks.filter(task => task.status === 'done').length,
    inReview: tasks.filter(task => task.status === 'in_review').length,
    total: tasks.length,
  }), [tasks]);
  const handleSubmit = async (values: TaskFormValues) => {
    try {
      if (formMode === 'create') {
        const created = await createTask(values);
        setTasks((prev) => [created, ...prev]);
      } else if (selectedTask) {
        const updated = await updateTask(selectedTask.id, values);
        setTasks((prev) => prev.map((task) => (task.id === updated.id ? updated : task)));
      }
      setSelectedTask(null);
      setFormMode('create');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể lưu công việc');
    }
  };

  const handleDelete = async (taskId: number) => {
    try {
      await deleteTask(taskId);
      setTasks((prev) => prev.filter((task) => task.id !== taskId));
      if (selectedTask?.id === taskId) {
        setSelectedTask(null);
        setFormMode('create');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể xóa công việc');
    }
  };

  // Logic xử lý kéo thả (truyền cho Board)
  const handleTaskMove = async (taskId: number, newStatus: Task['status']) => {
    const previousTasks = [...tasks];

    setTasks((prev) =>
      prev.map((task) =>
        task.id === taskId ? { ...task, status: newStatus as Task['status'] } : task
      )
    );

    try {
      await updateTaskStatus(taskId, newStatus);
    } catch (err) {
      setTasks(previousTasks);
      setError(err instanceof Error ? err.message : 'Không thể chuyển trạng thái công việc');
    }
  };

  const initialDepartment = user?.department_id ?? departments[0]?.id ?? 0;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Workspace quản lý"
        title="Công việc của nhóm"
        description="Tạo, phân công và theo dõi tiến độ công việc trong phòng ban."
        actions={<button type="button" className="button-secondary" onClick={() => void Promise.all([loadTasks(), loadReferences()])}>
          <Icon name="refresh" size={15} /> Tải lại
        </button>}
      />

      <div className="dashboard-stat-grid dashboard-stat-grid--compact">
        <StatCard icon="tasks" label="Task đang hiển thị" value={taskSummary.total} tone="blue" />
        <StatCard icon="sparkles" label="Chờ duyệt" value={taskSummary.inReview} tone="orange" />
        <StatCard icon="alert" label="Bị chặn" value={taskSummary.blocked} tone="red" />
        <StatCard icon="check" label="Hoàn thành" value={taskSummary.done} tone="green" />
      </div>

      <div className="filter-toolbar">
        <div className="toolbar-grid">
          <select value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1); }}>
            <option value="all">Tất cả trạng thái</option>
            <option value="todo">Cần làm</option>
            <option value="doing">Đang làm</option>
            <option value="in_review">Chờ duyệt</option>
            <option value="blocked">Bị chặn</option>
            <option value="done">Hoàn thành</option>
          </select>
          <select value={assigneeFilter} onChange={(event) => { setAssigneeFilter(event.target.value); setPage(1); }}>
            <option value="all">Tất cả người phụ trách</option>
            {visibleUsers.map((member) => (
              <option key={member.id} value={member.id}>
                {member.full_name}
              </option>
            ))}
          </select>
          <select value={overdueFilter} onChange={(event) => { setOverdueFilter(event.target.value as 'all' | 'true'); setPage(1); }}>
            <option value="all">Tất cả thời hạn</option>
            <option value="true">Chỉ công việc quá hạn</option>
          </select>
          <select value={projectFilter} onChange={(event) => { setProjectFilter(event.target.value); setPage(1); }}>
            <option value="all">Tất cả project</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>{project.code || project.name}</option>
            ))}
          </select>
        </div>
      </div>

      {error ? <div className="alert alert--error">{error}</div> : null}

      <section className="layout">
        <div className="layout__main">
          {loading ? (
            <div className="loading">Đang tải công việc của nhóm...</div>
          ) : (
            <Board
              tasks={tasks}
              onEdit={(task) => {
                setSelectedTask(task);
                setFormMode('edit');
                void handleProjectChange(task.project_id ?? null);
              }}
              onDelete={handleDelete}
              onTaskMove={handleTaskMove}
            />
          )}
        </div>
        
        <aside className="layout__side">
          <TaskForm
            mode={formMode}
            task={selectedTask}
            departments={departments.filter((department) => department.id === user?.department_id)}
            users={visibleUsers}
            referencesLoading={referencesLoading}
            projects={projects}
            projectMembers={projectMembers}
            onProjectChange={(projectId) => void handleProjectChange(projectId)}
            onSubmit={handleSubmit}
            onCancel={() => {
              setSelectedTask(null);
              setFormMode('create');
            }}
          />
          {formMode === 'create' && initialDepartment ? <p className="hint-text">Công việc mới sẽ được tạo trong phòng ban của bạn.</p> : null}
        </aside>
      </section>
      <PaginationControls page={page} pages={pages} total={total} onPageChange={setPage} />
    </div>
  );
}
