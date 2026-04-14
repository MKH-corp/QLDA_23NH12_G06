import { BOARD_COLUMNS } from '../constants/board';
import type { Task } from '../types/task';
import { Column } from './Column';

interface BoardProps {
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
}

export function Board({ tasks, onEdit, onDelete }: BoardProps) {
  return (
    <div className="board-grid">
      {BOARD_COLUMNS.map((column) => (
        <Column
          key={column.key}
          title={column.title}
          tasks={tasks.filter((task) => task.status === column.key)}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
