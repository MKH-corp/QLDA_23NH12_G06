import { useEffect, useMemo, useState } from 'react';

import { getDepartments, getUsers } from '../api/references';
import { createTask, deleteTask, getTasks, updateTask, updateTaskStatus } from '../api/tasks';
import { Board } from '../components/Board';
import { TaskForm } from '../components/TaskForm';
import type { DepartmentOption, UserOption } from '../types/reference';
import type { Task, TaskFormValues } from '../types/task';
import { useAuth } from '../context/AuthContext';

export function StaffTasksPage() {
  const { user } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [users, setUsers] = useState<UserOption[]>([]);
  
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  
  const [loading, setLoading] = useState(true);
  const [referencesLoading, setReferencesLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
      const data = await getTasks({});
      const myTasks = user?.id ? data.filter((task) => task.assignee_id === user.id) : data;
      setTasks(myTasks);
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
    if (user?.id) {
      void loadTasks();
    }
  }, [user?.id]);

  const visibleUsers = useMemo(
    () => users.filter((item) => item.department_id === user?.department_id),
    [users, user?.department_id]
  );

  const handleSubmit = async (values: TaskFormValues) => {
    try {
      if (selectedTask) {
        const updated = await updateTask(selectedTask.id, values);
        setTasks((prev) => prev.map((task) => (task.id === updated.id ? updated : task)));
      }
      setSelectedTask(null);
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
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete task');
    }
  };

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

      {/* 
        CHÌA KHÓA NẰM Ở ĐÂY: 
        Nếu không có task nào được chọn, ta đè CSS 'display: block' để xóa bỏ chia cột. 
        Bảng Kanban sẽ rộng 100% không bị che khuất! 
      */}
      <section 
        className="layout" 
        style={!selectedTask ? { display: 'block' } : undefined}
      >
        <div className="layout__main">
          {loading ? (
            <div className="loading">Loading your tasks...</div>
          ) : (
            <Board
              tasks={tasks}
              onEdit={(task) => {
                setSelectedTask(task);
                setFormMode('edit');
              }}
              onDelete={handleDelete}
              onTaskMove={handleTaskMove}
            />
          )}
        </div>

        {/* Form sẽ chỉ render (và chiếm chỗ) khi có selectedTask */}
        {selectedTask && (
          <aside className="layout__side">
            <TaskForm
              mode="edit"
              task={selectedTask}
              departments={departments.filter((department) => department.id === user?.department_id)}
              users={visibleUsers}
              referencesLoading={referencesLoading}
              onSubmit={handleSubmit}
              onCancel={() => {
                setSelectedTask(null);
              }}
            />
          </aside>
        )}
      </section>
    </div>
  );
}