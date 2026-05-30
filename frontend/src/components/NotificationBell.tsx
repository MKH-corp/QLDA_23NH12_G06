import { useState } from 'react';
import { getNotifications, markNotificationAsRead, runNotificationCheck } from '../api/services';
import { useFetch } from '../hooks/useApi';

export function NotificationBell() {
  const { data: notifications, refetch } = useFetch(getNotifications);
  const [isOpen, setIsOpen] = useState(false);

  const unreadCount = notifications?.filter(n => !n.is_read).length || 0;

  const handleMarkAsRead = async (id: number) => {
    await markNotificationAsRead(id);
    refetch(); // Cập nhật lại số đếm sau khi click
  };

  const handleToggle = async () => {
    const nextIsOpen = !isOpen;
    setIsOpen(nextIsOpen);

    if (nextIsOpen) {
      try {
        await runNotificationCheck();
      } catch (error) {
        console.error('Failed to refresh notifications:', error);
      } finally {
        await refetch();
      }
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <button className="icon-btn" onClick={handleToggle}>
        🔔
        {unreadCount > 0 && <span className="notify-badge">{unreadCount}</span>}
      </button>

      {isOpen && (
        <div className="glass-panel" style={{ position: 'absolute', right: 0, top: '50px', width: '320px', zIndex: 100, padding: '16px' }}>
          <h4 style={{ margin: '0 0 12px 0', borderBottom: '1px solid #e2e8f0', paddingBottom: '8px' }}>Notifications</h4>
          
          {notifications?.length === 0 ? (
            <p style={{ fontSize: '13px', color: '#64748b', textAlign: 'center' }}>No new notifications</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '300px', overflowY: 'auto' }}>
              {notifications?.map(note => (
                <div 
                  key={note.id} 
                  onClick={() => handleMarkAsRead(note.id)}
                  style={{ 
                    padding: '8px', 
                    borderRadius: '8px', 
                    background: note.is_read ? 'transparent' : '#f0fdf4',
                    cursor: 'pointer',
                    opacity: note.is_read ? 0.6 : 1
                  }}
                >
                  <strong style={{ fontSize: '13px', color: '#0f172a' }}>{note.title}</strong>
                  <p style={{ fontSize: '12px', color: '#64748b', margin: '4px 0 0 0' }}>{note.message}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
