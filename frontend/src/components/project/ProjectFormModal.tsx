import { useState, useEffect } from 'react';
import { ProjectCreate, ProjectListItem, ProjectStatus, ProjectPriority } from '../../types/project';

interface ProjectFormModalProps {
  project: ProjectListItem | null;
  onClose: () => void;
  onSubmit: (data: ProjectCreate) => Promise<void>;
}

export function ProjectFormModal({ project, onClose, onSubmit }: ProjectFormModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [departments, setDepartments] = useState<Array<{ id: number; name: string }>>([]);
  const [managers, setManagers] = useState<Array<{ id: number; full_name: string }>>([]);
  const [deptLoading, setDeptLoading] = useState(true);

  const getDefaultDepartmentId = (): number | undefined => {
    // Fetch from localStorage or use first available
    return undefined; // Will be loaded from departments list
  };

  const [formData, setFormData] = useState<ProjectCreate>({
    name: '',
    description: '',
    code: '',
    status: 'PLANNING' as ProjectStatus,
    priority: 'MEDIUM' as ProjectPriority,
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    department_id: undefined,
    manager_id: undefined,
  });

  // Load departments and managers on mount
  useEffect(() => {
    const loadDepts = async () => {
      try {
        setDeptLoading(true);
        // TODO: Replace with actual API call
        // const response = await fetch('/api/v1/departments');
        // const data = await response.json();
        // setDepartments(data);
        
        // For now, use mock data
        const mockDepts = [
          { id: 1, name: 'Sales' },
          { id: 2, name: 'Engineering' },
          { id: 3, name: 'HR' },
          { id: 4, name: 'Finance' },
        ];
        setDepartments(mockDepts);
        
        // Set default to first department
        setFormData(prev => ({ ...prev, department_id: mockDepts[0]?.id }));
      } catch (e) {
        console.error('Failed to load departments:', e);
      } finally {
        setDeptLoading(false);
      }
    };

    const loadManagers = async () => {
      try {
        // TODO: Replace with actual API call
        // const response = await fetch('/api/v1/users?role=manager');
        // const data = await response.json();
        // setManagers(data);
        
        const mockManagers = [
          { id: 1, full_name: 'Nguyễn Văn A' },
          { id: 2, full_name: 'Trần Thị B' },
          { id: 3, full_name: 'Lê Văn C' },
        ];
        setManagers(mockManagers);
      } catch (e) {
        console.error('Failed to load managers:', e);
      }
    };

    loadDepts();
    loadManagers();
  }, []);

  // When editing, populate form with project data
  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name,
        description: project.description || '',
        code: project.code || '',
        status: project.status as ProjectStatus,
        priority: project.priority as ProjectPriority,
        start_date: project.start_date 
          ? new Date(project.start_date).toISOString().split('T')[0]
          : '',
        end_date: project.end_date
          ? new Date(project.end_date).toISOString().split('T')[0]
          : '',
        department_id: undefined,  // Not in ProjectListItem response from backend
        manager_id: undefined,      // Not in ProjectListItem response from backend
      });
    }
  }, [project]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await onSubmit(formData);
      onClose();
    } catch (e: any) {
      setError(e.message || 'Lỗi khi lưu dự án');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof ProjectCreate, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'white',
          borderRadius: 12,
          width: '90%',
          maxWidth: 600,
          boxShadow: '0 20px 60px rgba(0,0,0,.3)',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ padding: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <h2 style={{ margin: 0, color: '#1e3a8a' }}>
              {project ? '✏️ Cập nhật Dự án' : '+ Tạo Dự án'}
            </h2>
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                fontSize: 24,
                cursor: 'pointer',
              }}
            >
              ✕
            </button>
          </div>

          {error && (
            <div style={{ background: '#fee2e2', color: '#991b1b', padding: 12, borderRadius: 8, marginBottom: 16 }}>
              ❌ {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 16 }}>
            {/* Name */}
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
                Tên dự án *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={e => handleChange('name', e.target.value)}
                placeholder="Nhập tên dự án"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 6,
                  fontSize: 14,
                  boxSizing: 'border-box',
                }}
                required
              />
            </div>

            {/* Code */}
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
                Mã dự án
              </label>
              <input
                type="text"
                value={formData.code}
                onChange={e => handleChange('code', e.target.value)}
                placeholder="VD: PROJ001"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 6,
                  fontSize: 14,
                  boxSizing: 'border-box',
                }}
              />
            </div>

            {/* Description */}
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
                Mô tả
              </label>
              <textarea
                value={formData.description}
                onChange={e => handleChange('description', e.target.value)}
                placeholder="Nhập mô tả dự án"
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 6,
                  fontSize: 14,
                  minHeight: 100,
                  fontFamily: 'inherit',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            {/* Status & Priority */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
                  Trạng thái
                </label>
                <select
                  value={formData.status}
                  onChange={e => handleChange('status', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: 6,
                    fontSize: 14,
                    boxSizing: 'border-box',
                  }}
                >
                  {['PLANNING', 'ACTIVE', 'ON_HOLD', 'REVIEW', 'COMPLETED', 'CANCELLED', 'ARCHIVED'].map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
                  Ưu tiên
                </label>
                <select
                  value={formData.priority}
                  onChange={e => handleChange('priority', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: 6,
                    fontSize: 14,
                    boxSizing: 'border-box',
                  }}
                >
                  {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(p => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Dates */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
                  Ngày bắt đầu *
                </label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={e => handleChange('start_date', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: 6,
                    fontSize: 14,
                    boxSizing: 'border-box',
                  }}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
                  Ngày kết thúc *
                </label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={e => handleChange('end_date', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    border: '1px solid #e2e8f0',
                    borderRadius: 6,
                    fontSize: 14,
                    boxSizing: 'border-box',
                  }}
                  required
                />
              </div>
            </div>

            {/* Department */}
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
                Phòng ban *
              </label>
              <input
                type="number"
                value={formData.department_id}
                onChange={e => handleChange('department_id', parseInt(e.target.value))}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 6,
                  fontSize: 14,
                  boxSizing: 'border-box',
                }}
                required
              />
            </div>

            {/* Buttons */}
            <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
              <button
                type="button"
                onClick={onClose}
                className="btn-outline"
                style={{ flex: 1 }}
              >
                Hủy
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-gradient"
                style={{ flex: 1, opacity: loading ? 0.6 : 1 }}
              >
                {loading ? 'Đang lưu...' : project ? '💾 Cập nhật' : '+ Tạo'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
