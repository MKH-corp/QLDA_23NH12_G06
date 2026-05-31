import { useEffect, useMemo, useState } from 'react';

import { getDepartments, getUsers } from '../api/references';
import { deleteTask, getTasks, updateTaskStatus } from '../api/tasks';
import { Board } from '../components/Board';
import { TaskForm } from '../components/TaskForm';
import { PaginationControls } from '../components/PaginationControls';
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
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);

  const loadReferences = async () => {
    setReferencesLoading(true);
    try {
      const [departmentData, userData] = await Promise.all([getDepartments(), getUsers()]);
      setDepartments(departmentData);
      setUsers(userData);
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
      const data = await getTasks({ page });
      const myTasks = user?.id ? data.items.filter((task) => task.assignee_id === user.id) : data.items;
      setTasks(myTasks);
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
    if (user?.id) {
      void loadTasks();
    }
  }, [user?.id, page]);

  const visibleUsers = useMemo(
    () => users.filter((item) => item.department_id === user?.department_id),
    [users, user?.department_id]
  );

  const handleSubmit = async (values: TaskFormValues) => {
    try {
      if (selectedTask) {
        const updated = await updateTaskStatus(selectedTask.id, values.status);
        setTasks((prev) => prev.map((task) => (task.id === updated.id ? updated : task)));
      }
      setSelectedTask(null);
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
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Không thể xóa công việc');
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
      setError(err instanceof Error ? err.message : 'Không thể chuyển trạng thái công việc');
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Staff</p>
          <h1>Công việc của tôi</h1>
          <p className="subtitle">Theo dõi và cập nhật các công việc được giao.</p>
        </div>
        <div className="toolbar-grid">
          <button type="button" className="button-secondary" onClick={() => void loadTasks()}>
            Tải lại
          </button>
        </div>
      </header>

      {error ? <div className="alert alert--error">{error}</div> : null}

      <section 
        className="layout" 
        style={!selectedTask ? { display: 'block' } : undefined}
      >
        <div className="layout__main">
          {loading ? (
            <div className="loading">Đang tải công việc...</div>
          ) : (
            <Board
              tasks={tasks}
              onEdit={(task) => {
                setSelectedTask(task);
                setFormMode('edit');
              }}
              onDelete={handleDelete}
              canDelete={false}
              onTaskMove={handleTaskMove}
            />
          )}
        </div>

        {selectedTask && (
          <aside className="layout__side">
            <TaskForm
              mode="edit"
              task={selectedTask}
              departments={departments.filter((department) => department.id === user?.department_id)}
              users={visibleUsers}
              referencesLoading={referencesLoading}
              hideProject
              hideDepartment
              hideAssignee
              onSubmit={handleSubmit}
              onCancel={() => {
                setSelectedTask(null);
              }}
            />
          </aside>
        )}
      </section>
      <PaginationControls page={page} pages={pages} total={total} onPageChange={setPage} />
    </div>
  );
}
