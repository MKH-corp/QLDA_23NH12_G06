import type { Task } from '../types/task';

interface TaskDetailProps {
  task: Task | null;
  onStatusChange?: (status: Task['status']) => void;
}

export function TaskDetail({ task, onStatusChange }: TaskDetailProps) {
  if (!task) {
    return <div className="panel-empty">Select a task to view its details.</div>;
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <p className="eyebrow">Task Detail</p>
          <h2>{task.title}</h2>
        </div>
      </div>

      <div className="detail-grid">
        <div>
          <strong>Status</strong>
          <p>{task.status}</p>
        </div>
        <div>
          <strong>Priority</strong>
          <p>{task.priority}</p>
        </div>
        <div>
          <strong>Deadline</strong>
          <p>{task.deadline || 'No deadline'}</p>
        </div>
        <div>
          <strong>Assignee ID</strong>
          <p>{task.assignee_id}</p>
        </div>
      </div>

      <div>
        <strong>Description</strong>
        <p>{task.description || 'No description'}</p>
      </div>

      {onStatusChange ? (
        <div className="status-actions">
          {(['todo', 'doing', 'blocked', 'done'] as Array<Task['status']>).map((status) => (
            <button key={status} type="button" className={task.status === status ? 'button-secondary' : ''} onClick={() => onStatusChange(status)}>
              Mark {status}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
