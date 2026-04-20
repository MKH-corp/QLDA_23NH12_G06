import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from './components/AppShell';
import { ProtectedRoute } from './components/ProtectedRoute';
import { RoleRedirectPage } from './pages/RoleRedirectPage';
import { LoginPage } from './pages/LoginPage';
import { StaffTasksPage } from './pages/StaffTasksPage';
import { ManagerTasksPage } from './pages/ManagerTasksPage';
import { AdminPage } from './pages/AdminPage';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/redirect-by-role" element={<RoleRedirectPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route element={<ProtectedRoute roles={['staff']} />}>
            <Route path="/staff/tasks" element={<StaffTasksPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['manager']} />}>
            <Route path="/manager/tasks" element={<ManagerTasksPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['admin']} />}>
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/redirect-by-role" replace />} />
      <Route path="*" element={<Navigate to="/redirect-by-role" replace />} />
    </Routes>
  );
}

export default App;
