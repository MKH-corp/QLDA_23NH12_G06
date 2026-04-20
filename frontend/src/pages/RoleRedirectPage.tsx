import { Navigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';

export function RoleRedirectPage() {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const path = user.role === 'admin' ? '/admin' : user.role === 'manager' ? '/manager/tasks' : '/staff/tasks';
  return <Navigate to={path} replace />;
}
