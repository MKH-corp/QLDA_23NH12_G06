export interface DepartmentOption {
  id: number;
  name: string;
}

export interface UserOption {
  id: number;
  full_name: string;
  email: string;
  role: 'admin' | 'manager' | 'staff';
  department_id: number;
  is_active: boolean;
  created_at: string;
}
