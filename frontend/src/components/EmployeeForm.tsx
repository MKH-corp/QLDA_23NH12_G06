import { useState, useEffect } from 'react';
import type { User, UserCreatePayload, UserUpdatePayload } from '../api/services';
import type { DepartmentOption } from '../types/reference';

interface EmployeeFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: UserCreatePayload | UserUpdatePayload) => Promise<void>;
  initialData?: User;
  departments: DepartmentOption[];
  isLoading?: boolean;
}

export function EmployeeForm({ isOpen, onClose, onSubmit, initialData, departments, isLoading }: EmployeeFormProps) {
  const isEditMode = !!initialData;
  const [formData, setFormData] = useState(() => 
    initialData ? {
      full_name: initialData.full_name,
      email: initialData.email,
      password: '',
      role: initialData.role as 'admin' | 'manager' | 'staff',
      department_id: initialData.department_id,
      is_active: initialData.is_active,
    } : {
      full_name: '',
      email: '',
      password: '',
      role: 'staff' as const,
      department_id: departments[0]?.id || 1,
      is_active: true,
    }
  );
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Update form data when initialData changes
  useEffect(() => {
    if (initialData) {
      setFormData({
        full_name: initialData.full_name,
        email: initialData.email,
        password: '',
        role: initialData.role as 'admin' | 'manager' | 'staff',
        department_id: initialData.department_id,
        is_active: initialData.is_active,
      });
    } else {
      // Reset form to empty when adding new employee
      setFormData({
        full_name: '',
        email: '',
        password: '',
        role: 'staff' as const,
        department_id: departments[0]?.id || 1,
        is_active: true,
      });
    }
  }, [initialData, departments]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await onSubmit(formData as any);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Đã xảy ra lỗi');
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '32px',
        width: '90%',
        maxWidth: '500px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
      }}>
        <h2 style={{ margin: '0 0 24px', color: '#1e3a8a' }}>
          {isEditMode ? 'Sửa nhân viên' : 'Thêm nhân viên'}
        </h2>

        {error && (
          <div style={{
            marginBottom: '16px',
            padding: '12px',
            backgroundColor: '#fee2e2',
            color: '#991b1b',
            borderRadius: '8px',
            fontSize: '14px',
          }}>
            ❌ {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Full Name */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: '#1e293b', fontSize: '14px' }}>
              Họ tên *
            </label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box',
              }}
              placeholder="John Doe"
            />
          </div>

          {/* Email */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: '#1e293b', fontSize: '14px' }}>
              Email *
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box',
              }}
              placeholder="john@example.com"
            />
          </div>

          {/* Password */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: '#1e293b', fontSize: '14px' }}>
              Mật khẩu {!isEditMode && '*'}
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password || ''}
                onChange={handleChange}
                required={!isEditMode}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #e2e8f0',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  paddingRight: '40px',
                }}
                placeholder={isEditMode ? 'Để trống nếu không đổi mật khẩu' : 'Nhập mật khẩu'}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '18px',
                }}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          {/* Role */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: '#1e293b', fontSize: '14px' }}>
              Vai trò *
            </label>
            <select
              name="role"
              value={formData.role || 'staff'}
              onChange={handleChange}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box',
              }}
            >
              <option value="staff">Staff</option>
              <option value="manager">Manager</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          {/* Department */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: '#1e293b', fontSize: '14px' }}>
              Phòng ban *
            </label>
            <select
              name="department_id"
              value={formData.department_id}
              onChange={handleChange}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                fontSize: '14px',
                boxSizing: 'border-box',
              }}
            >
              {departments.map(dept => (
                <option key={dept.id} value={dept.id}>{dept.name}</option>
              ))}
            </select>
          </div>

          {/* Is Active */}
          <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center' }}>
            <input
              type="checkbox"
              name="is_active"
              checked={formData.is_active || false}
              onChange={handleChange}
              style={{ marginRight: '8px', width: '18px', height: '18px', cursor: 'pointer' }}
            />
            <label style={{ fontWeight: 600, color: '#1e293b', fontSize: '14px', cursor: 'pointer' }}>
              Đang hoạt động
            </label>
          </div>

          {/* Buttons */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                flex: 1,
                padding: '10px',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                backgroundColor: '#f8fafc',
                color: '#1e293b',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '14px',
              }}
              disabled={isLoading}
            >
              Hủy
            </button>
            <button
              type="submit"
              style={{
                flex: 1,
                padding: '10px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: '#3b82f6',
                color: 'white',
                fontWeight: 600,
                cursor: 'pointer',
                fontSize: '14px',
                opacity: isLoading ? 0.6 : 1,
              }}
              disabled={isLoading}
            >
              {isLoading ? 'Đang lưu...' : isEditMode ? 'Cập nhật' : 'Tạo mới'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
