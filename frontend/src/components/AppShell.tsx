import { Link, Outlet } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';

export function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Sprint 2 Frontend</p>
          <h1 className="sidebar__title">Work & KPI</h1>
          <p className="sidebar__subtitle">Role-based dashboard</p>
        </div>

        <nav className="sidebar__nav">
          {user?.role === 'staff' ? <Link to="/staff/tasks">My Tasks</Link> : null}
          {user?.role === 'manager' ? <Link to="/manager/tasks">Team Tasks</Link> : null}
          {user?.role === 'admin' ? <Link to="/admin">Admin Management</Link> : null}
        </nav>

        <div className="sidebar__footer">
          <div>
            <strong>{user?.full_name}</strong>
            <p>{user?.email}</p>
            <span className="role-pill">{user?.role}</span>
          </div>
          <button type="button" className="button-secondary" onClick={logout}>
            Logout
          </button>
        </div>
      </aside>

      <main className="shell-content">
        <Outlet />
      </main>
    </div>
  );
}
