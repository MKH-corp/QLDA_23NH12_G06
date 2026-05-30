import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';

export function LoginPage() {
  const { login, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('an@company.local');
  const [password, setPassword] = useState('Password@123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (isAuthenticated && user) {
    const fallback = user.role === 'admin' ? '/admin' : user.role === 'manager' ? '/manager/tasks' : '/staff/tasks';
    return <Navigate to={fallback} replace />;
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login({ email, password });
      const destination = (location.state as { from?: string } | null)?.from;
      navigate(destination ?? '/redirect-by-role', { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Đăng nhập thất bại');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="screen-center">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div>
          <p className="eyebrow">Work & KPI</p>
          <h1>Đăng nhập</h1>
          <p className="subtitle">Sử dụng tài khoản công việc để truy cập hệ thống.</p>
        </div>

        {error ? <div className="alert alert--error">{error}</div> : null}

        <label>
          Email
          <input value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>

        <label>
          Mật khẩu
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </button>
      </form>
    </div>
  );
}
