import { NavLink, Outlet } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { ChatbotPanel } from './ChatbotPanel';
import { NotificationBell } from './NotificationBell';
import { RoleInsightsPanel } from './RoleInsightsPanel';

export function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Quản lý công việc</p>
          <h1 className="sidebar__title">Work & KPI</h1>
          <p className="sidebar__subtitle">Theo dõi hiệu suất theo vai trò</p>
        </div>

        <nav className="sidebar__nav">
          {user?.role === 'staff' ? <NavLink to="/staff/tasks">Công việc của tôi</NavLink> : null}
          {user?.role === 'manager' ? <NavLink to="/manager/tasks">Công việc của nhóm</NavLink> : null}
          {user?.role === 'admin' ? (
            <>
              <NavLink to="/admin" end>Tổng quan</NavLink>
              <NavLink to="/admin/employees">Nhân sự</NavLink>
              <NavLink to="/admin/projects">Dự án</NavLink>
              <NavLink to="/admin/reports">Báo cáo</NavLink>
              <NavLink to="/admin/kpi">Hiệu suất KPI</NavLink>
            </>
          ) : null}
        </nav>

        <div className="sidebar__footer">
          <div>
            <strong>{user?.full_name}</strong>
            <p>{user?.email}</p>
            <span className="role-pill">{user?.role}</span>
          </div>
          <button type="button" className="button-secondary" onClick={logout}>
            Đăng xuất
          </button>
        </div>
      </aside>

      <main className="shell-content">
        <div className="shell-toolbar">
          <RoleInsightsPanel />
          <NotificationBell />
        </div>
        <Outlet />
      </main>
      <ChatbotPanel />
    </div>
  );
}
