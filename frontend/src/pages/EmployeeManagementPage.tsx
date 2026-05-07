import { useState } from 'react';
import { getUsers, type User } from '../api/services';
import { useFetch } from '../hooks/useApi';
import { DataTable } from '../components/DataTable';

export function EmployeeManagementPage() {
  const [searchTerm, setSearchTerm] = useState('');
  // Sử dụng dependency array để tự động gọi lại API khi searchTerm thay đổi (thực tế nên dùng debounce)
  const { data: users, loading, error } = useFetch(() => getUsers(searchTerm), [searchTerm]);

  return (
    <div className="page-container">
      <header className="page-header glass-panel admin-topbar" style={{ marginBottom: '24px' }}>
        <div>
          <h2 style={{ margin: 0, color: '#1e3a8a' }}>👥 Employee Management</h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>Manage your workforce and assign roles</p>
        </div>
        
        <div style={{ display: 'flex', gap: '16px' }}>
          <div className="search-bar" style={{ width: '250px' }}>
            <span>🔍</span>
            <input 
              type="text" 
              placeholder="Search by name or email..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="btn-gradient">+ Add Employee</button>
        </div>
      </header>

      {error ? (
        <div className="glass-panel" style={{ color: 'red' }}>Error loading data: {error}</div>
      ) : (
        <div className="glass-panel">
          <DataTable
            title="All Employees"
            items={users || []}
            emptyText={loading ? "Loading employees..." : "No employees found matching your search."}
            columns={[
              { 
                key: 'user', 
                title: 'Employee', 
                render: (u) => (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#3b82f6', color: 'white', display: 'grid', placeItems: 'center', fontWeight: 'bold' }}>
                      {u.full_name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, color: '#1e293b' }}>{u.full_name}</div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>{u.email}</div>
                    </div>
                  </div>
                )
              },
              { key: 'role', title: 'Role', render: (u) => <span className={`badge badge--${u.role}`}>{u.role.toUpperCase()}</span> },
              { key: 'status', title: 'Status', render: (u) => (
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: u.is_active ? '#10b981' : '#ef4444' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: u.is_active ? '#10b981' : '#ef4444' }}></span>
                  {u.is_active ? 'Active' : 'Disabled'}
                </span>
              )},
              { key: 'actions', title: 'Actions', render: () => <button className="btn-outline" style={{ padding: '6px 12px' }}>Edit</button> }
            ]}
          />
        </div>
      )}
    </div>
  );
}