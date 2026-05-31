import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from './components/AppShell';
import { ProtectedRoute } from './components/ProtectedRoute';
import { RoleRedirectPage } from './pages/RoleRedirectPage';
import { LoginPage } from './pages/LoginPage';
import { StaffTasksPage } from './pages/StaffTasksPage';
import { ManagerTasksPage } from './pages/ManagerTasksPage';
import { AdminPage } from './pages/AdminPage';
import { EmployeeManagementPage } from './pages/EmployeeManagementPage';
import { ProjectManagementPage } from './pages/ProjectManagementPage';
import { MyProjectsPage } from './pages/MyProjectsPage';
import { ReportsPage } from './pages/ReportsPage';
import { KpiTrackingPage } from './pages/KpiTrackingPage';

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/redirect-by-role" element={<RoleRedirectPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route element={<ProtectedRoute roles={['staff']} />}>
            <Route path="/staff/tasks" element={<StaffTasksPage />} />
            <Route path="/staff/projects" element={<MyProjectsPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['manager']} />}>
            <Route path="/manager/tasks" element={<ManagerTasksPage />} />
            <Route path="/manager/projects" element={<ProjectManagementPage />} />
            <Route path="/manager/my-projects" element={<MyProjectsPage />} />
            <Route path="/manager/reports" element={<ReportsPage />} />
            <Route path="/manager/kpi" element={<KpiTrackingPage />} />
          </Route>

          <Route element={<ProtectedRoute roles={['admin']} />}>
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/admin/employees" element={<EmployeeManagementPage />} />
            <Route path="/admin/projects" element={<ProjectManagementPage />} />
            <Route path="/admin/reports" element={<ReportsPage />} />
            <Route path="/admin/kpi" element={<KpiTrackingPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/redirect-by-role" replace />} />
      <Route path="*" element={<Navigate to="/redirect-by-role" replace />} />
    </Routes>
  );
}

export default App;
