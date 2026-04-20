import { useEffect, useMemo, useState } from 'react';

import { getDepartments, getUsers } from './api/references';
import { createTask, deleteTask, getTasks, updateTask } from './api/tasks';
import { Board } from './components/Board';
import { TaskForm } from './components/TaskForm';
import type { DepartmentOption, UserOption } from './types/reference';
import type { Task, TaskFormValues } from './types/task';

function App() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [referencesLoading, setReferencesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');

  const sortedTasks = useMemo(
    () => [...tasks].sort((a, b) => Number(Boolean(a.deadline)) - Number(Boolean(b.deadline)) || a.id - b.id),
    [tasks],
  );

  const loadTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTasks();
      setTasks(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const loadReferences = async () => {
    setReferencesLoading(true);
    setError(null);
    try {
      const [departmentData, userData] = await Promise.all([getDepartments(), getUsers()]);
      setDepartments(departmentData);
      setUsers(userData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reference data');
    } finally {
      setReferencesLoading(false);
    }
  };

  useEffect(() => {
    void loadTasks();
    void loadReferences();
  }, []);

  const handleCreateClick = () => {
    setFormMode('create');
    setSelectedTask(null);
  };

  const handleEdit = (task: Task) => {
    setFormMode('edit');
    setSelectedTask(task);
  };

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

  const handleCancel = () => {
    setSelectedTask(null);
    setFormMode('create');
  };

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Sprint 1 Frontend</p>
          <h1>Work & KPI Management</h1>
          <p className="subtitle">Minimal Kanban board connected to FastAPI backend.</p>
        </div>
        <div className="page-header__actions">
          <button type="button" className="button-secondary" onClick={() => void Promise.all([loadTasks(), loadReferences()])}>
            Reload
          </button>
          <button type="button" onClick={handleCreateClick}>
            New Task
          </button>
        </div>
      </header>

      {error ? <div className="alert alert--error">{error}</div> : null}

      <section className="layout">
        <div className="layout__main">
          {loading ? <div className="loading">Loading tasks...</div> : <Board tasks={sortedTasks} onEdit={handleEdit} onDelete={handleDelete} />}
        </div>

        <aside className="layout__side">
          <TaskForm
            mode={formMode}
            task={selectedTask}
            departments={departments}
            users={users}
            referencesLoading={referencesLoading}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
          />
        </aside>
      </section>
    </main>
  );
}

export default App;
