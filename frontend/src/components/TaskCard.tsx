import { useDraggable } from '@dnd-kit/core';
import type { Task } from '../types/task';
import { Icon, StatusBadge } from './ui';

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  canDelete?: boolean;
  isOverlay?: boolean;
}

export function TaskCard({ task, onEdit, onDelete, canDelete = true, isOverlay = false }: TaskCardProps) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: task.id.toString(),
    data: { task },
    disabled: isOverlay,
  });

  const style: React.CSSProperties = {
    opacity: isDragging && !isOverlay ? 0.3 : 1,
    cursor: isOverlay ? 'grabbing' : 'grab',
    transform: isOverlay ? 'rotate(0deg) scale(1.02)' : undefined,
    boxShadow: isOverlay ? '0px 15px 25px rgba(0,0,0,0.15)' : undefined,
    width: isOverlay ? '280px' : undefined,
    backgroundColor: isOverlay ? '#ffffff' : undefined,
    zIndex: isOverlay ? 9999 : undefined,
    pointerEvents: isOverlay ? 'none' : 'auto',
  };

  return (
    <article
      className="task-card"
      ref={isOverlay ? undefined : setNodeRef}
      style={style}
      {...(isOverlay ? {} : attributes)}
      {...(isOverlay ? {} : listeners)}
    >
      <div className="task-card__head">
        <h4>{task.title}</h4>
        <span className={`badge badge--${task.priority.toLowerCase()}`}>{task.priority}</span>
      </div>

      <div className="task-card__meta-grid">
        <p><Icon name="calendar" size={14} />{formatDate(task.due_date)}</p>
        <p><Icon name="kpi" size={14} />Trọng số {task.base_weight}</p>
        {task.project_id ? <p><Icon name="folder" size={14} />Dự án #{task.project_id}</p> : null}
      </div>

      <div className="task-card__footer">
        <StatusBadge status={task.status} />
        <span className="task-card__assignee">NV #{task.assignee_id}</span>
      </div>
      
      <div className="task-card__actions">
        <button
          type="button"
          onClick={() => onEdit(task)}
          onPointerDown={(e) => e.stopPropagation()}
        >
          Sửa
        </button>
        {canDelete ? <button
          type="button"
          className="button-danger"
          onClick={() => onDelete(task.id)}
          onPointerDown={(e) => e.stopPropagation()}
        >
          Xóa
        </button> : null}
      </div>
    </article>
  );
}

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleDateString('vi-VN') : 'Chưa đặt hạn';
}
