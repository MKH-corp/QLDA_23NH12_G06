import type { ReactNode } from 'react';

export type IconName =
  | 'activity'
  | 'alert'
  | 'bell'
  | 'bot'
  | 'building'
  | 'calendar'
  | 'check'
  | 'dashboard'
  | 'folder'
  | 'kpi'
  | 'logout'
  | 'plus'
  | 'refresh'
  | 'reports'
  | 'search'
  | 'sparkles'
  | 'tasks'
  | 'users';

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    activity: <path d="M3 12h3l2-6 4 12 3-8 2 2h4" />,
    alert: <><path d="m12 3 9 16H3L12 3Z" /><path d="M12 9v4M12 16h.01" /></>,
    bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" /><path d="M10 21h4" /></>,
    bot: <><rect width="16" height="12" x="4" y="8" rx="3" /><path d="M12 4v4M8 12h.01M16 12h.01M8 16h8" /></>,
    building: <><path d="M4 21V5l8-3 8 3v16" /><path d="M9 21v-4h6v4M8 9h.01M12 9h.01M16 9h.01M8 13h.01M12 13h.01M16 13h.01" /></>,
    calendar: <><rect width="18" height="18" x="3" y="4" rx="2" /><path d="M16 2v4M8 2v4M3 10h18" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    dashboard: <><rect width="7" height="7" x="3" y="3" rx="1" /><rect width="7" height="7" x="14" y="3" rx="1" /><rect width="7" height="7" x="3" y="14" rx="1" /><rect width="7" height="7" x="14" y="14" rx="1" /></>,
    folder: <><path d="M3 6a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" /></>,
    kpi: <><path d="M4 19V9M10 19V5M16 19v-7M22 19H2" /></>,
    logout: <><path d="M10 17l5-5-5-5M15 12H3M21 19V5a2 2 0 0 0-2-2h-6" /></>,
    plus: <path d="M12 5v14M5 12h14" />,
    refresh: <><path d="M20 11a8.1 8.1 0 0 0-15.5-2M4 4v5h5M4 13a8.1 8.1 0 0 0 15.5 2M20 20v-5h-5" /></>,
    reports: <><path d="M4 19V5M4 19h16M8 16v-5M12 16V8M16 16v-8M20 16V4" /></>,
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></>,
    sparkles: <><path d="m12 3-1.5 4.5L6 9l4.5 1.5L12 15l1.5-4.5L18 9l-4.5-1.5ZM5 16l-.7 2.3L2 19l2.3.7L5 22l.7-2.3L8 19l-2.3-.7ZM19 15l-.7 2.3L16 18l2.3.7L19 21l.7-2.3L22 18l-2.3-.7Z" /></>,
    tasks: <><path d="m9 11 3 3L22 4" /><path d="M21 12v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h11" /></>,
    users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" /></>,
  };

  return (
    <svg
      aria-hidden="true"
      className="ui-icon"
      fill="none"
      height={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
      viewBox="0 0 24 24"
      width={size}
    >
      {paths[name]}
    </svg>
  );
}

export function PageHeader({
  actions,
  description,
  eyebrow,
  title,
}: {
  actions?: ReactNode;
  description: string;
  eyebrow: string;
  title: string;
}) {
  return (
    <header className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="subtitle">{description}</p>
      </div>
      {actions ? <div className="page-heading__actions">{actions}</div> : null}
    </header>
  );
}

export function StatCard({
  hint,
  icon,
  label,
  tone = 'blue',
  value,
}: {
  hint?: string;
  icon: IconName;
  label: string;
  tone?: 'blue' | 'green' | 'orange' | 'purple' | 'red';
  value: ReactNode;
}) {
  return (
    <article className={`stat-card stat-card--${tone}`}>
      <span className="stat-card__icon"><Icon name={icon} size={20} /></span>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        {hint ? <small>{hint}</small> : null}
      </div>
    </article>
  );
}

const STATUS_LABELS: Record<string, string> = {
  blocked: 'Bị chặn',
  doing: 'Đang làm',
  done: 'Hoàn thành',
  in_review: 'Chờ duyệt',
  todo: 'Cần làm',
};

export function StatusBadge({ status }: { status: string }) {
  return <span className={`status-badge status-badge--${status.toLowerCase()}`}>{STATUS_LABELS[status] ?? status}</span>;
}

export function EmptyState({ action, description, title }: { action?: ReactNode; description: string; title: string }) {
  return (
    <div className="empty-state">
      <span><Icon name="folder" size={22} /></span>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}

export function Skeleton({ rows = 3 }: { rows?: number }) {
  return <div className="skeleton-stack">{Array.from({ length: rows }, (_, index) => <span key={index} />)}</div>;
}

export function ConfirmModal({
  description,
  onCancel,
  onConfirm,
  open,
  title,
}: {
  description: string;
  onCancel: () => void;
  onConfirm: () => void;
  open: boolean;
  title: string;
}) {
  if (!open) return null;
  return (
    <div className="confirm-backdrop" onClick={onCancel}>
      <section className="confirm-modal" onClick={event => event.stopPropagation()}>
        <span className="confirm-modal__icon"><Icon name="alert" /></span>
        <h3>{title}</h3>
        <p>{description}</p>
        <div className="confirm-modal__actions">
          <button type="button" className="button-secondary" onClick={onCancel}>Hủy</button>
          <button type="button" className="button-danger-solid" onClick={onConfirm}>Xác nhận</button>
        </div>
      </section>
    </div>
  );
}
