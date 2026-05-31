import { useEffect, useMemo, useState } from 'react';

import type { DepartmentOption, UserOption } from '../types/reference';
import type { AssignableUser, ProjectListItem } from '../types/project';
import type { Task, TaskFormValues } from '../types/task';
import { toTaskFormValues } from '../utils/task';

interface TaskFormProps {
  mode: 'create' | 'edit';
  task?: Task | null;
  departments: DepartmentOption[];
  users: UserOption[];
  referencesLoading: boolean;
  projects?: ProjectListItem[];
  projectsLoading?: boolean;
  hideProject?: boolean;
  fixedProjectId?: number | null;
  projectMembers?: AssignableUser[];
  onProjectChange?: (projectId: number | null) => void;
  hideDepartment?: boolean;
  hideAssignee?: boolean;
  onSubmit: (values: TaskFormValues) => Promise<void>;
  onCancel: () => void;
}

export function TaskForm({
  mode,
  task,
  departments,
  users,
  referencesLoading,
  projects = [],
  projectsLoading = false,
  hideProject = false,
  fixedProjectId,
  projectMembers = [],
  onProjectChange,
  hideDepartment = false,
  hideAssignee = false,
  onSubmit,
  onCancel,
}: TaskFormProps) {
  const [values, setValues] = useState<TaskFormValues>(toTaskFormValues(task));
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setValues({ ...toTaskFormValues(task), project_id: fixedProjectId ?? task?.project_id ?? null });
  }, [task, fixedProjectId]);

  useEffect(() => {
    if (departments.length === 0 || (!values.project_id && users.length === 0)) {
      return;
    }

    setValues((prev) => {
      const nextDepartmentId = departments.some((department) => department.id === prev.department_id)
        ? prev.department_id
        : departments[0].id;

      const availableUsers = prev.project_id ? projectMembers : users.filter((user) => user.department_id === nextDepartmentId);
      const nextAssigneeId = availableUsers.some((user) => user.id === prev.assignee_id)
        ? prev.assignee_id
        : (availableUsers[0]?.id ?? prev.assignee_id);

      return {
        ...prev,
        department_id: nextDepartmentId,
        assignee_id: nextAssigneeId,
      };
    });
  }, [departments, users, projectMembers, values.project_id]);

  const filteredProjects = useMemo(
    () => projects.filter(
      (project) =>
        !['COMPLETED', 'CANCELLED', 'ARCHIVED'].includes(project.status)
        && (!project.department_id || project.department_id === values.department_id),
    ),
    [projects, values.department_id],
  );

  const assigneeUsers = useMemo(
    () => values.project_id ? projectMembers : users.filter((user) => user.department_id === values.department_id),
    [projectMembers, users, values.department_id, values.project_id],
  );

  const handleChange = (field: keyof TaskFormValues, value: string | number) => {
    setValues((prev) => ({ ...prev, [field]: value }));
  };

  const handleDepartmentChange = (departmentId: number) => {
    const filteredUsers = users.filter((user) => user.department_id === departmentId);
    const fallbackUserId = filteredUsers[0]?.id ?? 0;
    const currentProject = projects.find((project) => project.id === values.project_id);
    const projectId = currentProject && currentProject.department_id === departmentId ? currentProject.id : null;
    if (!projectId) onProjectChange?.(null);

    setValues((prev) => ({
      ...prev,
      department_id: departmentId,
      project_id: projectId,
      assignee_id: filteredUsers.some((user) => user.id === prev.assignee_id) ? prev.assignee_id : fallbackUserId,
    }));
  };

  const handleProjectChange = (projectId: number | null) => {
    const project = projects.find((item) => item.id === projectId);
    onProjectChange?.(projectId);
    setValues((prev) => ({
      ...prev,
      project_id: projectId,
      department_id: project?.department_id ?? prev.department_id,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({
        ...values,
        base_weight: Number(values.base_weight),
        assignee_id: Number(values.assignee_id),
        department_id: Number(values.department_id),
        project_id: values.project_id ? Number(values.project_id) : null,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <div className="task-form__header">
        <h3>{mode === 'create' ? 'Tạo công việc' : 'Sửa công việc'}</h3>
      </div>

      <label>
        Tiêu đề
        <input
          value={values.title}
          onChange={(event) => handleChange('title', event.target.value)}
          required
          placeholder="Nhập tiêu đề công việc"
        />
      </label>

      <label>
        Mô tả
        <textarea
          value={values.description}
          onChange={(event) => handleChange('description', event.target.value)}
          rows={3}
          placeholder="Mô tả ngắn"
        />
      </label>

      <div className="task-form__grid">
        <label>
          Trạng thái
          <select value={values.status} onChange={(event) => handleChange('status', event.target.value)}>
            <option value="in_review">Chờ duyệt</option>
            <option value="todo">Cần làm</option>
            <option value="doing">Đang làm</option>
            <option value="blocked">Bị chặn</option>
            <option value="done">Hoàn thành</option>
          </select>
        </label>

        <label>
          Thời hạn
          <input type="date" value={values.deadline} onChange={(event) => handleChange('deadline', event.target.value)} />
        </label>

        <label>
          Trọng số ưu tiên
          <input
            type="number"
            min={1}
            max={10}
            value={values.base_weight}
            onChange={(event) => handleChange('base_weight', Number(event.target.value))}
          />
        </label>

        {!hideDepartment ? (
          <label>
            Phòng ban
            <select
              value={values.department_id}
              onChange={(event) => handleDepartmentChange(Number(event.target.value))}
              disabled={referencesLoading || departments.length === 0}
            >
              {departments.map((department) => (
                <option key={department.id} value={department.id}>
                  {department.name}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        {!hideProject ? (
          <label>
            Project
            <select
              value={values.project_id ?? ''}
              onChange={(event) => handleProjectChange(event.target.value ? Number(event.target.value) : null)}
              disabled={projectsLoading || fixedProjectId != null}
            >
              <option value="">Không thuộc project</option>
              {filteredProjects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.code || `PRJ-${project.id}`} - {project.name}
                </option>
              ))}
            </select>
          </label>
        ) : null}

        {!hideAssignee ? (
          <label>
            Người phụ trách
            <select
              value={values.assignee_id}
              onChange={(event) => handleChange('assignee_id', Number(event.target.value))}
              disabled={referencesLoading || assigneeUsers.length === 0}
            >
              {assigneeUsers.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.full_name} ({user.email})
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>

      {values.project_id && assigneeUsers.length === 0 ? (
        <div className="alert alert--error">Project chưa có thành viên. Hãy thêm thành viên trước khi giao task.</div>
      ) : null}

      <div className="task-form__actions">
        <button type="button" className="button-secondary" onClick={onCancel}>
          Hủy
        </button>
        <button type="submit" disabled={submitting || referencesLoading || (!hideAssignee && assigneeUsers.length === 0)}>
          {submitting ? 'Đang lưu...' : mode === 'create' ? 'Tạo mới' : 'Lưu thay đổi'}
        </button>
      </div>
    </form>
  );
}
