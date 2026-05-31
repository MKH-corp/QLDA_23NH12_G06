import { useDroppable } from '@dnd-kit/core';
import type { BoardStatus, Task } from '../types/task';
import { TaskCard } from './TaskCard';

interface ColumnProps {
  id: BoardStatus;
  title: string;
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  canDelete?: boolean;
}

export function Column({ id, title, tasks, onEdit, onDelete, canDelete = true }: ColumnProps) {
  const { isOver, setNodeRef } = useDroppable({ id });

  return (
    <section 
      className={`board-column board-column--${id} ${isOver ? 'board-column--active' : ''}`}
      ref={setNodeRef}
    >
      <div className="board-column__header">
        <h3><span className="board-column__dot" />{title}</h3>
        <span>{tasks.length}</span>
      </div>

      <div className="board-column__body">
        {tasks.length === 0 ? (
          <div className="board-column__empty">Chưa có công việc</div>
        ) : (
          tasks.map((task) => (
            <TaskCard 
              key={task.id} 
              task={task} 
              onEdit={onEdit} 
              onDelete={onDelete} 
              canDelete={canDelete}
            />
          ))
        )}
      </div>
    </section>
  );
}
