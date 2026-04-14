import { useEffect, useState } from 'react';

import type { Task, TaskFormValues } from '../types/task';
import { toTaskFormValues } from '../utils/task';

interface TaskFormProps {
  mode: 'create' | 'edit';
  task?: Task | null;
  onSubmit: (values: TaskFormValues) => Promise<void>;
  onCancel: () => void;
}

export function TaskForm({ mode, task, onSubmit, onCancel }: TaskFormProps) {
  const [values, setValues] = useState<TaskFormValues>(toTaskFormValues(task));
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setValues(toTaskFormValues(task));
  }, [task]);

  const handleChange = (field: keyof TaskFormValues, value: string | number) => {
    setValues((prev) => ({ ...prev, [field]: value }));
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
            <option value="done">Done</option>
            <option value="blocked">Blocked</option>
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
          Creator ID
          <input
            type="number"
            min={1}
            value={values.creator_id}
            onChange={(event) => handleChange('creator_id', Number(event.target.value))}
          />
        </label>

        <label>
          Assignee ID
          <input
            type="number"
            min={1}
            value={values.assignee_id}
            onChange={(event) => handleChange('assignee_id', Number(event.target.value))}
          />
        </label>

        <label>
          Department ID
          <input
            type="number"
            min={1}
            value={values.department_id}
            onChange={(event) => handleChange('department_id', Number(event.target.value))}
          />
        </label>
      </div>

      <div className="task-form__actions">
        <button type="button" className="button-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" disabled={submitting}>
          {submitting ? 'Saving...' : mode === 'create' ? 'Create' : 'Save changes'}
        </button>
      </div>
    </form>
  );
}
