import { apiRequest } from './client';
import type { DepartmentOption, UserOption } from '../types/reference';

/**
 * Lấy danh sách phòng ban dùng cho dropdown (form task, filter...)
 * Dùng endpoint /references/* được thiết kế riêng cho reference data
 * Hoạt động với mọi role: admin, manager, staff
 */
export function getDepartments(): Promise<DepartmentOption[]> {
  return apiRequest<DepartmentOption[]>('/references/departments');
}

/**
 * Lấy danh sách user dùng cho dropdown chọn assignee
 * Backend tự lọc theo role:
 *   - admin: tất cả users
 *   - manager: chỉ users trong dept của mình
 *   - staff: chỉ bản thân
 */
export function getUsers(): Promise<UserOption[]> {
  return apiRequest<UserOption[]>('/references/users');
}