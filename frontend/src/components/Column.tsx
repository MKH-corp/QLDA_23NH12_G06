import { useDroppable } from '@dnd-kit/core';
import type { Task } from '../types/task';
import { TaskCard } from './TaskCard';

interface ColumnProps {
  id: string; // 1. THÊM MỚI: Định danh cho cột (chính là status của DB, VD: 'TODO')
  title: string;
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  canDelete?: boolean;
}

export function Column({ id, title, tasks, onEdit, onDelete, canDelete = true }: ColumnProps) {
  // 2. Khai báo hook useDroppable
  const { isOver, setNodeRef } = useDroppable({
    id: id, // Phải truyền đúng id của cột vào đây
  });

  return (
    <section 
      className={`board-column ${isOver ? 'board-column--active' : ''}`} // Thêm class tùy chọn khi hover
      ref={setNodeRef} // 3. Gắn ref vào vùng HTML chứa cột để báo cho dnd-kit biết đây là bãi đáp
      style={{
        // 4. (UX) Đổi màu nền nhẹ khi đang kéo một thẻ lơ lửng trên cột này
        backgroundColor: isOver ? 'var(--bg-hover-color, #f1f5f9)' : undefined,
        transition: 'background-color 0.2s ease',
      }}
    >
      <div className="board-column__header">
        <h3>{title}</h3>
        <span>{tasks.length}</span>
      </div>

      <div className="board-column__body">
        {tasks.length === 0 ? (
          <div className="board-column__empty">No tasks</div>
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
