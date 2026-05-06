import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import type { Task } from '../types/task';

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
}

export function TaskCard({ task, onEdit, onDelete }: TaskCardProps) {
  // 1. Khai báo hook useDraggable để biến Component này thành vật thể kéo được
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: task.id.toString(), // dnd-kit bắt buộc ID phải là dạng chuỗi (string)
    data: { task }, // Gửi kèm data của task để sau này thả xuống cột sẽ lấy ra dùng
  });

  // 2. Cấu hình style chuyển động khi kéo
  const style = {
    // translate giúp thẻ di chuyển mượt mà đi theo con trỏ chuột
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0.4 : 1, // Mờ đi một chút khi đang lơ lửng trên không
    cursor: isDragging ? 'grabbing' : 'grab', // Đổi icon con trỏ chuột thành hình bàn tay nắm lại
  };

  return (
    <article 
      className="task-card"
      ref={setNodeRef} // 3. Chỉ định đây là phần tử HTML sẽ nhận thao tác kéo
      style={style}    // 4. Áp dụng style chuyển động
      {...attributes}  // 5. Thêm các thuộc tính hỗ trợ đọc màn hình (Accessibility)
      {...listeners}   // 6. Lắng nghe sự kiện click/giữ chuột
    >
      <div className="task-card__head">
        <h4>{task.title}</h4>
        <span className={`badge badge--${task.priority.toLowerCase()}`}>{task.priority}</span>
      </div>
      
      <p className="task-card__meta">Due: {task.due_date || 'No deadline'}</p>
      
      <div className="task-card__actions">
        {/* 
          7. QUAN TRỌNG: Thêm onPointerDown chặn sự kiện nổi bọt. 
          Giúp dnd-kit hiểu là "Đang bấm nút, không phải kéo thẻ đâu, đừng can thiệp!" 
        */}
        <button 
          type="button" 
          onClick={() => onEdit(task)}
          onPointerDown={(e) => e.stopPropagation()} 
        >
          Edit
        </button>
        
        <button 
          type="button" 
          className="button-danger" 
          onClick={() => onDelete(task.id)}
          onPointerDown={(e) => e.stopPropagation()}
        >
          Delete
        </button>
      </div>
    </article>
  );
}