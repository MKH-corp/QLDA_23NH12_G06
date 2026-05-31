import { NavLink, Outlet, useLocation } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { ChatbotPanel } from './ChatbotPanel';
import { NotificationBell } from './NotificationBell';
import { RoleInsightsPanel } from './RoleInsightsPanel';
import { Icon, type IconName } from './ui';

const TITLES: Record<string, string> = {
  '/admin': 'Tổng quan hệ thống',
  '/admin/employees': 'Quản lý nhân sự',
  '/admin/kpi': 'Hiệu suất KPI',
  '/admin/projects': 'Quản lý dự án',
  '/admin/reports': 'Báo cáo hiệu suất',
  '/manager/kpi': 'Hiệu suất KPI',
  '/manager/my-projects': 'Dự án của tôi',
  '/manager/projects': 'Quản lý dự án',
  '/manager/reports': 'Báo cáo hiệu suất',
  '/manager/tasks': 'Công việc của nhóm',
  '/staff/projects': 'Dự án của tôi',
  '/staff/tasks': 'Công việc của tôi',
};

const NAV_ITEMS: Record<string, Array<{ icon: IconName; label: string; to: string; end?: boolean }>> = {
  admin: [
    { icon: 'dashboard', label: 'Tổng quan', to: '/admin', end: true },
    { icon: 'users', label: 'Nhân sự', to: '/admin/employees' },
    { icon: 'folder', label: 'Dự án', to: '/admin/projects' },
    { icon: 'reports', label: 'Báo cáo', to: '/admin/reports' },
    { icon: 'kpi', label: 'Hiệu suất KPI', to: '/admin/kpi' },
  ],
  manager: [
    { icon: 'tasks', label: 'Công việc của nhóm', to: '/manager/tasks' },
    { icon: 'folder', label: 'Quản lý dự án', to: '/manager/projects' },
    { icon: 'activity', label: 'Dự án của tôi', to: '/manager/my-projects' },
    { icon: 'reports', label: 'Báo cáo', to: '/manager/reports' },
    { icon: 'kpi', label: 'Hiệu suất KPI', to: '/manager/kpi' },
  ],
  staff: [
    { icon: 'folder', label: 'Dự án của tôi', to: '/staff/projects' },
    { icon: 'tasks', label: 'Công việc của tôi', to: '/staff/tasks' },
  ],
};

export function AppShell() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const currentTitle = TITLES[location.pathname] ?? 'Work & KPI';
  const navItems = user ? NAV_ITEMS[user.role] ?? [] : [];
  const initials = user?.full_name
    .split(' ')
    .slice(-2)
    .map(part => part[0])
    .join('')
    .toUpperCase();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <span className="sidebar__logo"><Icon name="kpi" size={20} /></span>
          <div>
            <h1 className="sidebar__title">Work & KPI</h1>
            <p className="sidebar__subtitle">Workspace hiệu suất</p>
          </div>
        </div>

        <p className="sidebar__section-label">Không gian làm việc</p>
        <nav className="sidebar__nav">
          {navItems.map(item => (
            <NavLink key={item.to} to={item.to} end={item.end}>
              <Icon name={item.icon} size={17} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__footer">
          <div className="sidebar__profile">
            <span className="avatar">{initials}</span>
            <div>
              <strong>{user?.full_name}</strong>
              <p>{user?.email}</p>
              <span className="role-pill">{user?.role}</span>
            </div>
          </div>
          <button type="button" className="sidebar__logout" onClick={logout}>
            <Icon name="logout" size={16} /> Đăng xuất
          </button>
        </div>
      </aside>

      <main className="shell-content">
        <div className="shell-toolbar">
          <div>
            <p className="shell-toolbar__breadcrumb">Workspace / {user?.role}</p>
            <strong>{currentTitle}</strong>
          </div>
          <div className="shell-toolbar__actions">
            <ChatbotPanel />
            <RoleInsightsPanel />
            <NotificationBell />
            <span className="toolbar-avatar avatar">{initials}</span>
          </div>
        </div>
        <Outlet />
      </main>
    </div>
  );
}
