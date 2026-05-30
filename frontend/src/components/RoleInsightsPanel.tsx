import { useEffect, useState } from 'react';

import { getMyAIInsights, getTeamAIInsights, type AIInsight } from '../api/ai';
import { useAuth } from '../context/AuthContext';

export function RoleInsightsPanel() {
  const { user } = useAuth();
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [error, setError] = useState('');

  const loadInsights = async () => {
    if (!user) return;
    try {
      const result = user.role === 'staff' ? await getMyAIInsights() : await getTeamAIInsights();
      setInsights(result);
      setError('');
    } catch {
      setError('Không thể tải insight.');
    }
  };

  useEffect(() => {
    void loadInsights();
  }, [user?.id, user?.role]);

  return (
    <div className="floating-menu">
      <button type="button" className="button-secondary" onClick={() => setIsOpen((current) => !current)}>
        Insight theo vai trò
      </button>
      {isOpen ? (
        <div className="glass-panel floating-menu__panel insight-panel">
          <h4>Gợi ý dành cho {user?.role}</h4>
          {error ? <p className="alert alert--error">{error}</p> : null}
          {insights.length === 0 ? <p className="empty-copy">Chưa có cảnh báo hoặc gợi ý mới.</p> : null}
          {insights.slice(0, 4).map((insight, index) => (
            <article className={`insight-card insight-card--${insight.severity}`} key={`${insight.title}-${index}`}>
              <strong>{insight.title}</strong>
              <p>{insight.message}</p>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}
