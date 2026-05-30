import { useState } from 'react';

import { getNotifications, markNotificationAsRead } from '../api/services';
import { PaginationControls } from './PaginationControls';

export function NotificationBell() {
  const [notifications, setNotifications] = useState<Awaited<ReturnType<typeof getNotifications>> | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');

  const loadNotifications = async (nextPage = page) => {
    try {
      const result = await getNotifications(nextPage);
      setNotifications(result);
      setPage(nextPage);
      setError('');
    } catch {
      setError('Không thể tải thông báo.');
    }
  };

  const handleMarkAsRead = async (id: number) => {
    await markNotificationAsRead(id);
    await loadNotifications();
  };

  const handleToggle = async () => {
    const nextIsOpen = !isOpen;
    setIsOpen(nextIsOpen);
    if (nextIsOpen) await loadNotifications(1);
  };

  const unreadCount = notifications?.unread_count ?? 0;

  return (
    <div className="floating-menu">
      <button type="button" className="icon-btn" onClick={() => void handleToggle()} aria-label="Mở thông báo">
        🔔
        {unreadCount > 0 ? <span className="notify-badge">{unreadCount}</span> : null}
      </button>

      {isOpen ? (
        <div className="glass-panel floating-menu__panel notification-panel">
          <h4>Thông báo</h4>
          {error ? <p className="alert alert--error">{error}</p> : null}
          {!notifications?.items.length ? (
            <p className="empty-copy">Chưa có thông báo.</p>
          ) : (
            <div className="notification-list">
              {notifications.items.map((note) => (
                <button
                  type="button"
                  key={note.id}
                  onClick={() => void handleMarkAsRead(note.id)}
                  className={`notification-item ${note.is_read ? 'notification-item--read' : ''}`}
                >
                  <strong>{note.title}</strong>
                  <span>{note.message}</span>
                </button>
              ))}
            </div>
          )}
          {notifications ? (
            <PaginationControls
              page={notifications.page}
              pages={notifications.pages}
              total={notifications.total}
              onPageChange={(nextPage) => void loadNotifications(nextPage)}
            />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
