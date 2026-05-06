import { useEffect, useState } from 'react';

import { getTasks, updateTaskStatus } from '../api/tasks';
import { Board } from '../components/Board';
import type { Task } from '../types/task';
import { useAuth } from '../context/AuthContext';

export function StaffTasksPage() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Gọi API lấy task (Không truyền assignee_id để tránh lỗi TypeScript)
      const data = await getTasks({});
      
      // 2. Dùng code lọc ra những task thuộc về user hiện tại
      const myTasks = user?.id ? data.filter(task => task.assignee_id === user.id) : data;
      
      setTasks(myTasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.id) {
      void loadTasks();
    }
  }, [user?.id]);

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
      setError(err instanceof Error ? err.message : 'Failed to move task');
    }
  };

  const handleEdit = (task: Task) => {
    console.log("Edit task:", task.id);
  };

  const handleDelete = (taskId: number) => {
    console.log("Delete task:", taskId);
  };

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Staff</p>
          <h1>My Tasks</h1>
          <p className="subtitle">View and manage tasks assigned to you.</p>
        </div>
        <div className="toolbar-grid">
          <button type="button" className="button-secondary" onClick={() => void loadTasks()}>
            Reload
          </button>
        </div>
      </header>

      {error ? <div className="alert alert--error">{error}</div> : null}

      <section className="layout">
        <div className="layout__main" style={{ width: '100%' }}>
          {loading ? (
            <div className="loading">Loading your tasks...</div>
          ) : (
            <Board
              tasks={tasks}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onTaskMove={handleTaskMove}
            />
          )}
        </div>
      </section>
    </div>
  );
}