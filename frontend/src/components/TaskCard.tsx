import { useDraggable } from '@dnd-kit/core';
import type { Task } from '../types/task';

interface TaskCardProps {
  task: Task;
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  isOverlay?: boolean; // Cờ báo hiệu thẻ Bóng ma
}

export function TaskCard({ task, onEdit, onDelete, isOverlay = false }: TaskCardProps) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: task.id.toString(),
    data: { task },
    disabled: isOverlay, // Bóng ma thì không cần tính toán logic kéo thả nữa
  });

  // GIA CỐ STYLE ĐỂ BÓNG MA KHÔNG BỊ TÀNG HÌNH
  const style: React.CSSProperties = {
    // Thẻ gốc thì mờ đi 30% lúc bị kéo
    opacity: isDragging && !isOverlay ? 0.3 : 1,
    cursor: isOverlay ? 'grabbing' : 'grab',
    // Bóng ma thì nghiêng 3 độ và có đổ bóng
    transform: isOverlay ? 'rotate(0deg) scale(1.02)' : undefined,
    boxShadow: isOverlay ? '0px 15px 25px rgba(0,0,0,0.15)' : undefined,
    
    // --- 4 DÒNG QUAN TRỌNG ĐỂ CỨU BÓNG MA ---
    width: isOverlay ? '280px' : undefined, // Ép cứng chiều rộng giống trong cột
    backgroundColor: isOverlay ? '#ffffff' : undefined, // Nền trắng để không bị trong suốt
    zIndex: isOverlay ? 9999 : undefined, // Nổi lên trên cùng (đè lên header, menu...)
    pointerEvents: isOverlay ? 'none' : 'auto', // Tránh chuột vướng vào thẻ lúc đang kéo
  };

  return (
    <article
      className="task-card"
      ref={isOverlay ? undefined : setNodeRef} // Bóng ma thì bỏ ref
      style={style} // Áp dụng style mới
      {...(isOverlay ? {} : attributes)}
      {...(isOverlay ? {} : listeners)}
    >
      <div className="task-card__head">
        <h4>{task.title}</h4>
        <span className={`badge badge--${task.priority.toLowerCase()}`}>{task.priority}</span>
      </div>
      
      <p className="task-card__meta">Thời hạn: {task.due_date || 'Chưa đặt'}</p>
      
      <div className="task-card__actions">
        <button
          type="button"
          onClick={() => onEdit(task)}
          onPointerDown={(e) => e.stopPropagation()}
        >
          Sửa
        </button>
        <button
          type="button"
          className="button-danger"
          onClick={() => onDelete(task.id)}
          onPointerDown={(e) => e.stopPropagation()}
        >
          Xóa
        </button>
      </div>
    </article>
  );
}
