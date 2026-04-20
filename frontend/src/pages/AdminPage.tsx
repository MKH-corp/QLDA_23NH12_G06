import { useEffect, useState } from 'react';

import { getDepartments, getUsers } from '../api/references';
import { DataTable } from '../components/DataTable';
import type { DepartmentOption, UserOption } from '../types/reference';

export function AdminPage() {
  const [users, setUsers] = useState<UserOption[]>([]);
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [departmentData, userData] = await Promise.all([getDepartments(), getUsers()]);
      setDepartments(departmentData);
      setUsers(userData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load admin data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Admin</p>
          <h1>Management</h1>
          <p className="subtitle">Basic management view for users and departments.</p>
        </div>
        <button type="button" className="button-secondary" onClick={() => void loadData()}>
          Reload
        </button>
      </header>

      {error ? <div className="alert alert--error">{error}</div> : null}
      {loading ? <div className="loading">Loading admin data...</div> : null}

      {!loading ? (
        <div className="stacked-panels">
          <DataTable
            title="Departments"
            items={departments}
            emptyText="No departments found."
            columns={[
              { key: 'id', title: 'ID', render: (department) => department.id },
              { key: 'name', title: 'Name', render: (department) => department.name },
            ]}
          />
          <DataTable
            title="Users"
            items={users}
            emptyText="No users found."
            columns={[
              { key: 'id', title: 'ID', render: (member) => member.id },
              { key: 'name', title: 'Full name', render: (member) => member.full_name },
              { key: 'email', title: 'Email', render: (member) => member.email },
              { key: 'role', title: 'Role', render: (member) => member.role },
              { key: 'department', title: 'Department ID', render: (member) => member.department_id },
              { key: 'active', title: 'Active', render: (member) => (member.is_active ? 'Yes' : 'No') },
            ]}
          />
        </div>
      ) : null}
    </div>
  );
}
