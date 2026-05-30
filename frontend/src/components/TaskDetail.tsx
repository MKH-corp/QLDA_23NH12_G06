import type { Task } from '../types/task';

interface TaskDetailProps {
  task: Task | null;
  onStatusChange?: (status: Task['status']) => void;
}

export function TaskDetail({ task, onStatusChange }: TaskDetailProps) {
  if (!task) {
    return <div className="panel-empty">Chọn một công việc để xem chi tiết.</div>;
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <p className="eyebrow">Chi tiết công việc</p>
          <h2>{task.title}</h2>
        </div>
      </div>

      <div className="detail-grid">
        <div>
          <strong>Trạng thái</strong>
          <p>{task.status}</p>
        </div>
        <div>
          <strong>Ưu tiên</strong>
          <p>{task.priority}</p>
        </div>
        <div>
          <strong>Thời hạn</strong>
          <p>{task.deadline || 'Chưa đặt'}</p>
        </div>
        <div>
          <strong>ID người phụ trách</strong>
          <p>{task.assignee_id}</p>
        </div>
      </div>

      <div>
        <strong>Mô tả</strong>
        <p>{task.description || 'Chưa có mô tả'}</p>
      </div>

      {onStatusChange ? (
        <div className="status-actions">
          {(['todo', 'doing', 'blocked', 'done'] as Array<Task['status']>).map((status) => (
            <button key={status} type="button" className={task.status === status ? 'button-secondary' : ''} onClick={() => onStatusChange(status)}>
              Chuyển sang {status}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}
