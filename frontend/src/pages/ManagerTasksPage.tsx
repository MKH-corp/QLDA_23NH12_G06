import { useEffect, useMemo, useState } from 'react';

import { getDepartments, getUsers } from '../api/references';
import { createTask, deleteTask, getTasks, updateTask } from '../api/tasks';
import { Board } from '../components/Board';
import { TaskForm } from '../components/TaskForm';
import type { DepartmentOption, UserOption } from '../types/reference';
import type { Task, TaskFormValues } from '../types/task';
import { useAuth } from '../context/AuthContext';

export function ManagerTasksPage() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [loading, setLoading] = useState(true);
  const [referencesLoading, setReferencesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [assigneeFilter, setAssigneeFilter] = useState<string>('all');
  const [overdueFilter, setOverdueFilter] = useState<'all' | 'true'>('all');

  const loadReferences = async () => {
    setReferencesLoading(true);
    try {
      const [departmentData, userData] = await Promise.all([getDepartments(), getUsers()]);
      setDepartments(departmentData);
      setUsers(userData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load references');
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
      });
      setTasks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadReferences();
  }, []);

  useEffect(() => {
    void loadTasks();
  }, [statusFilter, overdueFilter]);

  const visibleUsers = useMemo(() => users.filter((item) => item.department_id === user?.department_id), [users, user?.department_id]);
  const filteredTasks = useMemo(() => {
    if (assigneeFilter === 'all') return tasks;
    return tasks.filter((task) => String(task.assignee_id) === assigneeFilter);
  }, [tasks, assigneeFilter]);

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
      setError(err instanceof Error ? err.message : 'Failed to save task');
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
      setError(err instanceof Error ? err.message : 'Failed to delete task');
    }
  };

  const initialDepartment = user?.department_id ?? departments[0]?.id ?? 0;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Manager</p>
          <h1>Team Tasks</h1>
          <p className="subtitle">Create, assign, and monitor tasks within your department.</p>
        </div>
        <div className="toolbar-grid">
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="all">All statuses</option>
            <option value="todo">Todo</option>
            <option value="doing">Doing</option>
            <option value="blocked">Blocked</option>
            <option value="done">Done</option>
          </select>
          <select value={assigneeFilter} onChange={(event) => setAssigneeFilter(event.target.value)}>
            <option value="all">All assignees</option>
            {visibleUsers.map((member) => (
              <option key={member.id} value={member.id}>
                {member.full_name}
              </option>
            ))}
          </select>
          <select value={overdueFilter} onChange={(event) => setOverdueFilter(event.target.value as 'all' | 'true')}>
            <option value="all">All deadlines</option>
            <option value="true">Overdue only</option>
          </select>
          <button type="button" className="button-secondary" onClick={() => void Promise.all([loadTasks(), loadReferences()])}>
            Reload
          </button>
        </div>
      </header>

      {error ? <div className="alert alert--error">{error}</div> : null}

      <section className="layout">
        <div className="layout__main">
          {loading ? <div className="loading">Loading team tasks...</div> : <Board tasks={filteredTasks} onEdit={(task) => {
            setSelectedTask(task);
            setFormMode('edit');
          }} onDelete={handleDelete} />}
        </div>
        <aside className="layout__side">
          <TaskForm
            mode={formMode}
            task={selectedTask}
            departments={departments.filter((department) => department.id === user?.department_id)}
            users={visibleUsers}
            referencesLoading={referencesLoading}
            onSubmit={handleSubmit}
            onCancel={() => {
              setSelectedTask(null);
              setFormMode('create');
            }}
          />
          {formMode === 'create' && initialDepartment ? <p className="hint-text">New tasks will be created inside your department.</p> : null}
        </aside>
      </section>
    </div>
  );
}
