import type { Task } from '../types/task';
import { TaskCard } from './TaskCard';

interface ColumnProps {
  title: string;
  tasks: Task[];
  onEdit: (task: Task) => void;
  onDelete: (taskId: number) => void;
}

export function Column({ title, tasks, onEdit, onDelete }: ColumnProps) {
  return (
    <section className="board-column">
      <div className="board-column__header">
        <h3>{title}</h3>
        <span>{tasks.length}</span>
      </div>

      <div className="board-column__body">
        {tasks.length === 0 ? (
          <div className="board-column__empty">No tasks</div>
        ) : (
          tasks.map((task) => <TaskCard key={task.id} task={task} onEdit={onEdit} onDelete={onDelete} />)
        )}
      </div>
    </section>
  );
}
