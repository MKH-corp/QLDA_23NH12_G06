import { useState } from 'react';
import { 
  DndContext, 
  DragEndEvent, 
  DragStartEvent, 
  PointerSensor, 
  useSensor, 
  useSensors, 
  closestCorners,
  DragOverlay 
} from '@dnd-kit/core';
import { restrictToWindowEdges } from '@dnd-kit/modifiers';
import { BOARD_COLUMNS } from '../constants/board';
import type { Task } from '../types/task';
import { Column } from './Column';
import { TaskCard } from './TaskCard';

interface BoardProps {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
  canDelete?: boolean;
  onTaskMove?: (taskId: number, newStatus: Task['status']) => void;
}

export function Board({ tasks, onEdit, onDelete, canDelete = true, onTaskMove }: BoardProps) {
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5, 
      },
    })
  );

  const handleDragStart = (event: DragStartEvent) => {
    const taskId = Number(event.active.id);
    const task = tasks.find((t) => t.id === taskId);
    if (task) {
      setActiveTask(task);
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveTask(null); 
    const { active, over } = event;

    if (!over) return;

    const taskId = Number(active.id);
    const newStatus = String(over.id) as Task['status'];

    const currentTask = tasks.find((t) => t.id === taskId);
    
    if (currentTask && currentTask.status !== newStatus) {
      if (onTaskMove) {
        onTaskMove(taskId, newStatus);
      } else {
        console.warn("⚠️ Bảng này chưa được truyền hàm onTaskMove để xử lý API!");
      }
    }
  };

  return (
    <DndContext 
      sensors={sensors} 
      collisionDetection={closestCorners} 
      onDragStart={handleDragStart} 
      onDragEnd={handleDragEnd}
    >
      <div className="board-grid">
        {BOARD_COLUMNS.map((column) => (
          <Column
            key={column.key}
            id={column.key}
            title={column.title}
            tasks={tasks.filter((task) => task.status === column.key)}
            onEdit={onEdit}
            onDelete={onDelete}
            canDelete={canDelete}
          />
        ))}
      </div>

      <DragOverlay modifiers={[restrictToWindowEdges]}>
        {activeTask ? (
          <div style={{ width: '280px', pointerEvents: 'none' }}>
            <TaskCard 
              task={activeTask} 
              onEdit={onEdit} 
              onDelete={onDelete} 
              canDelete={canDelete}
              isOverlay={true} 
            />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
