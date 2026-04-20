import { useEffect, useMemo, useState } from 'react';

import type { DepartmentOption, UserOption } from '../types/reference';
import type { Task, TaskFormValues } from '../types/task';
import { toTaskFormValues } from '../utils/task';

interface TaskFormProps {
  mode: 'create' | 'edit';
  task?: Task | null;
  departments: DepartmentOption[];
  users: UserOption[];
  referencesLoading: boolean;
  onSubmit: (values: TaskFormValues) => Promise<void>;
  onCancel: () => void;
}

export function TaskForm({ mode, task, departments, users, referencesLoading, onSubmit, onCancel }: TaskFormProps) {
  const [values, setValues] = useState<TaskFormValues>(toTaskFormValues(task));
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setValues(toTaskFormValues(task));
  }, [task]);

  useEffect(() => {
    if (departments.length === 0 || users.length === 0) {
      return;
    }

    setValues((prev) => {
      const nextDepartmentId = departments.some((department) => department.id === prev.department_id)
        ? prev.department_id
        : departments[0].id;

      const departmentUsers = users.filter((user) => user.department_id === nextDepartmentId);
      const nextCreatorId = departmentUsers.some((user) => user.id === prev.creator_id)
        ? prev.creator_id
        : (departmentUsers[0]?.id ?? prev.creator_id);
      const nextAssigneeId = departmentUsers.some((user) => user.id === prev.assignee_id)
        ? prev.assignee_id
        : (departmentUsers[0]?.id ?? prev.assignee_id);

      return {
        ...prev,
        department_id: nextDepartmentId,
        creator_id: nextCreatorId,
        assignee_id: nextAssigneeId,
      };
    });
  }, [departments, users]);

  const departmentUsers = useMemo(
    () => users.filter((user) => user.department_id === values.department_id),
    [users, values.department_id],
  );

  const handleChange = (field: keyof TaskFormValues, value: string | number) => {
    setValues((prev) => ({ ...prev, [field]: value }));
  };

  const handleDepartmentChange = (departmentId: number) => {
    const filteredUsers = users.filter((user) => user.department_id === departmentId);
    const fallbackUserId = filteredUsers[0]?.id ?? 0;

    setValues((prev) => ({
      ...prev,
      department_id: departmentId,
      creator_id: filteredUsers.some((user) => user.id === prev.creator_id) ? prev.creator_id : fallbackUserId,
      assignee_id: filteredUsers.some((user) => user.id === prev.assignee_id) ? prev.assignee_id : fallbackUserId,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({
        ...values,
        base_weight: Number(values.base_weight),
        creator_id: Number(values.creator_id),
        assignee_id: Number(values.assignee_id),
        department_id: Number(values.department_id),
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <div className="task-form__header">
        <h3>{mode === 'create' ? 'Create Task' : 'Edit Task'}</h3>
      </div>

      <label>
        Title
        <input
          value={values.title}
          onChange={(event) => handleChange('title', event.target.value)}
          required
          placeholder="Enter task title"
        />
      </label>

      <label>
        Description
        <textarea
          value={values.description}
          onChange={(event) => handleChange('description', event.target.value)}
          rows={3}
          placeholder="Short task description"
        />
      </label>

      <div className="task-form__grid">
        <label>
          Status
          <select value={values.status} onChange={(event) => handleChange('status', event.target.value)}>
            <option value="todo">Todo</option>
            <option value="doing">Doing</option>
            <option value="blocked">Blocked</option>
            <option value="done">Done</option>
          </select>
        </label>

        <label>
          Due date
          <input
            type="date"
            value={values.deadline}
            onChange={(event) => handleChange('deadline', event.target.value)}
          />
        </label>

        <label>
          Priority weight
          <input
            type="number"
            min={1}
            max={5}
            value={values.base_weight}
            onChange={(event) => handleChange('base_weight', Number(event.target.value))}
          />
        </label>

        <label>
          Department
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

        <label>
          Creator
          <select
            value={values.creator_id}
            onChange={(event) => handleChange('creator_id', Number(event.target.value))}
            disabled={referencesLoading || departmentUsers.length === 0}
          >
            {departmentUsers.map((user) => (
              <option key={user.id} value={user.id}>
                {user.full_name} ({user.email})
              </option>
            ))}
          </select>
        </label>

        <label>
          Assignee
          <select
            value={values.assignee_id}
            onChange={(event) => handleChange('assignee_id', Number(event.target.value))}
            disabled={referencesLoading || departmentUsers.length === 0}
          >
            {departmentUsers.map((user) => (
              <option key={user.id} value={user.id}>
                {user.full_name} ({user.email})
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="task-form__actions">
        <button type="button" className="button-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" disabled={submitting || referencesLoading || departments.length === 0 || departmentUsers.length === 0}>
          {submitting ? 'Saving...' : mode === 'create' ? 'Create' : 'Save changes'}
        </button>
      </div>
    </form>
  );
}
