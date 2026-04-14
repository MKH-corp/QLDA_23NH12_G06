import type { Task } from '../types/task';

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
}

export function TaskCard({ task, onEdit, onDelete }: TaskCardProps) {
  return (
    <article className="task-card">
      <div className="task-card__head">
        <h4>{task.title}</h4>
        <span className={`badge badge--${task.priority.toLowerCase()}`}>{task.priority}</span>
      </div>
      <p className="task-card__meta">Due: {task.due_date || 'No deadline'}</p>
      <div className="task-card__actions">
        <button type="button" onClick={() => onEdit(task)}>
          Edit
        </button>
        <button type="button" className="button-danger" onClick={() => onDelete(task.id)}>
          Delete
        </button>
      </div>
    </article>
  );
}
