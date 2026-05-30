import { useState, useEffect } from 'react';
import { getUsers, createUser, updateUser, deleteUser, type User, type UserCreatePayload, type UserUpdatePayload } from '../api/services';
import { useFetch } from '../hooks/useApi';
import { DataTable } from '../components/DataTable';
import { EmployeeForm } from '../components/EmployeeForm';
import { getDepartments } from '../api/references';
import type { DepartmentOption } from '../types/reference';
import { PaginationControls } from '../components/PaginationControls';

export function EmployeeManagementPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | undefined>(undefined);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [departments, setDepartments] = useState<DepartmentOption[]>([]);
  const [page, setPage] = useState(1);

  const { data: users, loading, error, refetch } = useFetch(
    () => getUsers(searchTerm, page),
    [searchTerm, page]
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
        setSuccessMessage('Đã cập nhật nhân viên.');
      } else {
        await createUser(formData as UserCreatePayload);
        setSuccessMessage('Đã tạo nhân viên.');
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
    if (!window.confirm(`Bạn có chắc muốn xóa ${user.full_name}?`)) {
      return;
    }

    try {
      await deleteUser(user.id);
      setSuccessMessage('Đã xóa nhân viên.');
      await refetch();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err: any) {
      console.error('Delete error:', err);
      alert(`Không thể xóa nhân viên: ${err.message}`);
    }
  };

  const handleToggleStatus = async (user: User) => {
    try {
      await updateUser(user.id, { is_active: !user.is_active });
      setSuccessMessage(user.is_active ? 'Đã vô hiệu hóa nhân viên.' : 'Đã kích hoạt nhân viên.');
      await refetch();
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err: any) {
      console.error('Status toggle error:', err);
      alert(`Không thể cập nhật trạng thái nhân viên: ${err.message}`);
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
          <h2 style={{ margin: 0, color: '#1e3a8a' }}>Quản lý nhân sự</h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#64748b' }}>Quản lý tài khoản, phòng ban và phân quyền.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '16px' }}>
          <div className="search-bar" style={{ width: '250px' }}>
            <span>🔍</span>
            <input 
              type="text" 
              placeholder="Tìm theo tên hoặc email..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
            />
          </div>
          <button 
            className="btn-gradient"
            onClick={handleAddClick}
            style={{ cursor: 'pointer' }}
          >
            + Thêm nhân viên
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
          Không thể tải dữ liệu: {error}
        </div>
      )}

      {/* Data Table */}
      <div className="glass-panel">
        <DataTable
          title="Danh sách nhân viên"
          items={users?.items || []}
          emptyText={loading ? "Đang tải nhân viên..." : "Không tìm thấy nhân viên phù hợp."}
          columns={[
            { 
              key: 'user', 
              title: 'Nhân viên',
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
              title: 'Phòng ban',
              render: (u) => (
                <span style={{ fontSize: '13px', color: '#475569' }}>
                  {u.department_name || `Dept ${u.department_id}`}
                </span>
              )
            },
            { key: 'role', title: 'Vai trò', render: (u) => <span className={`badge badge--${u.role}`}>{u.role.toUpperCase()}</span> },
            { key: 'status', title: 'Trạng thái', render: (u) => (
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
                title="Nhấn để đổi trạng thái"
              >
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: u.is_active ? '#10b981' : '#ef4444' }}></span>
                {u.is_active ? 'Đang hoạt động' : 'Đã vô hiệu hóa'}
              </span>
            )},
            { 
              key: 'actions', 
              title: 'Thao tác',
              render: (u) => (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    className="btn-outline" 
                    style={{ padding: '6px 12px', cursor: 'pointer' }}
                    onClick={() => handleEditClick(u)}
                  >
                    Sửa
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
                    Xóa
                  </button>
                </div>
              )
            }
          ]}
        />
      </div>
      {users ? <PaginationControls page={users.page} pages={users.pages} total={users.total} onPageChange={setPage} /> : null}

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
