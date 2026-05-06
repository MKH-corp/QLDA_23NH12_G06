import { DndContext, DragEndEvent, PointerSensor, useSensor, useSensors, closestCorners } from '@dnd-kit/core';
import { BOARD_COLUMNS } from '../constants/board';
import type { Task } from '../types/task';
import { Column } from './Column';

interface BoardProps {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  // THÊM DẤU ? ĐỂ TRÁNH LỖI CRASH WEB NẾU PAGE QUÊN TRUYỀN HÀM
  onTaskMove?: (taskId: number, newStatus: Task['status']) => void; 
}

export function Board({ tasks, onEdit, onDelete, onTaskMove }: BoardProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5, 
      },
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over) return;

    const taskId = Number(active.id);
    const newStatus = String(over.id) as Task['status'];

    const currentTask = tasks.find((t) => t.id === taskId);
    
    if (currentTask && currentTask.status !== newStatus) {
      // KIỂM TRA XEM COMPONENT CHA CÓ TRUYỀN HÀM XUỐNG KHÔNG RỒI MỚI GỌI
      if (onTaskMove) {
        onTaskMove(taskId, newStatus);
      } else {
        console.warn("⚠️ Bảng này chưa được truyền hàm onTaskMove để xử lý API!");
      }
    }
  };

  return (
    <DndContext sensors={sensors} collisionDetection={closestCorners} onDragEnd={handleDragEnd}>
      <div className="board-grid">
        {BOARD_COLUMNS.map((column) => (
          <Column
            key={column.key}
            id={column.key}
            title={column.title}
            tasks={tasks.filter((task) => task.status === column.key)}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </div>
    </DndContext>
  );
}