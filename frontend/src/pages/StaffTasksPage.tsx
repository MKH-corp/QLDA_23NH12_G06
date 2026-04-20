import { useEffect, useMemo, useState } from 'react';

import { getTask, getTasks, updateTaskStatus } from '../api/tasks';
import { Board } from '../components/Board';
import { TaskDetail } from '../components/TaskDetail';
import type { Task } from '../types/task';

export function StaffTasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTasks(statusFilter === 'all' ? undefined : { status: statusFilter });
      setTasks(data);
      if (selectedTask) {
        const refreshed = data.find((task) => task.id === selectedTask.id) ?? null;
        setSelectedTask(refreshed);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTasks();
  }, [statusFilter]);

  const sortedTasks = useMemo(
    () => [...tasks].sort((a, b) => Number(Boolean(a.deadline)) - Number(Boolean(b.deadline)) || a.id - b.id),
    [tasks],
  );

  const handleSelectTask = async (task: Task) => {
    try {
      const detail = await getTask(task.id);
      setSelectedTask(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load task detail');
    }
  };

  const handleStatusChange = async (status: Task['status']) => {
    if (!selectedTask) return;
    try {
      const updated = await updateTaskStatus(selectedTask.id, status);
      setSelectedTask(updated);
      setTasks((prev) => prev.map((task) => (task.id === updated.id ? updated : task)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task status');
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Staff</p>
          <h1>My Tasks</h1>
          <p className="subtitle">View assigned work, filter by status, and update your task progress.</p>
        </div>
        <div className="page-header__actions">
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="all">All statuses</option>
            <option value="todo">Todo</option>
            <option value="doing">Doing</option>
            <option value="blocked">Blocked</option>
            <option value="done">Done</option>
          </select>
          <button type="button" className="button-secondary" onClick={() => void loadTasks()}>
            Reload
          </button>
        </div>
      </header>

      {error ? <div className="alert alert--error">{error}</div> : null}

      <section className="layout">
        <div className="layout__main">
          {loading ? <div className="loading">Loading tasks...</div> : <Board tasks={sortedTasks} onEdit={handleSelectTask} onDelete={() => undefined} />}
        </div>
        <aside className="layout__side">
          <TaskDetail task={selectedTask} onStatusChange={handleStatusChange} />
        </aside>
      </section>
    </div>
  );
}
