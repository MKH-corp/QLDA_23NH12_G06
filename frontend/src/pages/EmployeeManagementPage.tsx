import { useState, useEffect, useCallback } from 'react';
import { getUsers, createUser, updateUser, deleteUser, type User, type UserCreatePayload, type UserUpdatePayload } from '../api/services';
import { useFetch } from '../hooks/useApi';
import { DataTable } from '../components/DataTable';
import { EmployeeForm } from '../components/EmployeeForm';
import { getDepartments } from '../api/references';
import type { DepartmentOption } from '../types/reference';

export function EmployeeManagementPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);

  const { data: users, loading, error, refetch } = useFetch(
    () => getUsers(searchTerm),
    [searchTerm]
  );

  // Load departments on mount
  useEffect(() => {
    getDepartments()
      .then(setDepartments)
      .catch(err => console.error('Failed to load departments:', err));
  }, []);

  const handleAddClick = () => {
    setEditingUser(undefined);
    setIsFormOpen(true);
  };

  const handleEditClick = (user: User) => {
    setEditingUser(user);
    setIsFormOpen(true);
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setEditingUser(undefined);
  };

  const handleFormSubmit = async (formData: UserCreatePayload | UserUpdatePayload) => {
    setIsSubmitting(true);
    try {
      if (editingUser) {
        await updateUser(editingUser.id, formData as UserUpdatePayload);
        setSuccessMessage('✅ Employee updated successfully!');
      } else {
        await createUser(formData as UserCreatePayload);
        setSuccessMessage('✅ Employee created successfully!');
      }
      
      // Refresh the list
      await refetch();
      handleFormClose();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err: any) {
      console.error('Form submission error:', err);
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (user: User) => {
    if (!window.confirm(`Are you sure you want to delete ${user.full_name}?`)) {
      return;
    }

    try {
      await deleteUser(user.id);
      setSuccessMessage('✅ Employee deleted successfully!');
      await refetch();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err: any) {
      console.error('Delete error:', err);
      alert(`Failed to delete employee: ${err.message}`);
    }
  };

  const handleToggleStatus = async (user: User) => {
    try {
      await updateUser(user.id, { is_active: !user.is_active });
      setSuccessMessage(user.is_active ? '✅ Employee disabled!' : '✅ Employee enabled!');
      await refetch();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err: any) {
      console.error('Status toggle error:', err);
      alert(`Failed to update employee status: ${err.message}`);
    }
  };

  return (
    <div className="page-container">
      {/* Success Message */}
      {successMessage && (
        <div style={{
          marginBottom: '16px',
          padding: '12px 16px',
          backgroundColor: '#dcfce7',
          color: '#166534',
          borderRadius: '8px',
          border: '1px solid #bbf7d0',
          fontSize: '14px',
          animation: 'slideIn 0.3s ease-out',
        }}>
          {successMessage}
        </div>
      )}

      {/* Header */}
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
          <button 
            className="btn-gradient"
            onClick={handleAddClick}
            style={{ cursor: 'pointer' }}
          >
            + Add Employee
          </button>
        </div>
      </header>

      {/* Error Display */}
      {error && (
        <div className="glass-panel" style={{ 
          color: '#991b1b', 
          backgroundColor: '#fee2e2', 
          border: '1px solid #fecaca',
          padding: '12px',
          borderRadius: '8px',
          marginBottom: '16px'
        }}>
          ❌ Error loading data: {error}
        </div>
      )}

      {/* Data Table */}
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
            { 
              key: 'department', 
              title: 'Department', 
              render: (u) => (
                <span style={{ fontSize: '13px', color: '#475569' }}>
                  {u.department_name || `Dept ${u.department_id}`}
                </span>
              )
            },
            { key: 'role', title: 'Role', render: (u) => <span className={`badge badge--${u.role}`}>{u.role.toUpperCase()}</span> },
            { key: 'status', title: 'Status', render: (u) => (
              <span 
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '6px', 
                  fontSize: '13px', 
                  color: u.is_active ? '#10b981' : '#ef4444',
                  cursor: 'pointer'
                }}
                onClick={() => handleToggleStatus(u)}
                title="Click to toggle status"
              >
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: u.is_active ? '#10b981' : '#ef4444' }}></span>
                {u.is_active ? 'Active' : 'Disabled'}
              </span>
            )},
            { 
              key: 'actions', 
              title: 'Actions', 
              render: (u) => (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    className="btn-outline" 
                    style={{ padding: '6px 12px', cursor: 'pointer' }}
                    onClick={() => handleEditClick(u)}
                  >
                    ✏️ Edit
                  </button>
                  <button 
                    className="btn-outline" 
                    style={{ 
                      padding: '6px 12px', 
                      cursor: 'pointer',
                      color: '#ef4444',
                      borderColor: '#fca5a5'
                    }}
                    onClick={() => handleDelete(u)}
                  >
                    🗑️ Delete
                  </button>
                </div>
              )
            }
          ]}
        />
      </div>

      {/* Employee Form Modal */}
      <EmployeeForm
        isOpen={isFormOpen}
        onClose={handleFormClose}
        onSubmit={handleFormSubmit}
        initialData={editingUser}
        departments={departments}
        isLoading={isSubmitting}
      />
    </div>
  );
}