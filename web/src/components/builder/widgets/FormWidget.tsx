import { useMemo, useState } from 'react';
import { ActionButton } from './ActionButton';

export interface FormFieldOption {
  value: string;
  label: string;
}

export interface FormField {
  id: string;
  label: string;
  type: 'text' | 'textarea' | 'number' | 'select';
  placeholder?: string;
  required?: boolean;
  options?: FormFieldOption[];
}

interface FormWidgetProps {
  title: string;
  description?: string;
  fields: FormField[];
  submitLabel?: string;
  onSubmit: (values: Record<string, string>) => void;
}

export function FormWidget({
  title,
  description,
  fields,
  submitLabel = 'Submit',
  onSubmit,
}: FormWidgetProps) {
  const initialValues = useMemo(() => {
    const values: Record<string, string> = {};
    for (const field of fields) {
      values[field.id] = '';
    }
    return values;
  }, [fields]);

  const [values, setValues] = useState<Record<string, string>>(initialValues);

  const updateValue = (fieldId: string, value: string) => {
    setValues((prev) => ({ ...prev, [fieldId]: value }));
  };

  const submit = () => {
    onSubmit(values);
  };

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
      <p className="text-sm font-semibold text-slate-100">{title}</p>
      {description ? <p className="mt-1 text-xs text-slate-400">{description}</p> : null}
      <div className="mt-3 space-y-2">
        {fields.map((field) => (
          <label key={field.id} className="block">
            <span className="mb-1 block text-xs text-slate-400">{field.label}</span>
            {field.type === 'textarea' ? (
              <textarea
                rows={3}
                required={field.required}
                value={values[field.id] ?? ''}
                placeholder={field.placeholder}
                onChange={(event) => updateValue(field.id, event.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-100 outline-none ring-0 transition focus:border-sky-500"
              />
            ) : field.type === 'select' ? (
              <select
                required={field.required}
                value={values[field.id] ?? ''}
                onChange={(event) => updateValue(field.id, event.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-100 outline-none ring-0 transition focus:border-sky-500"
              >
                <option value="">Select...</option>
                {(field.options ?? []).map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={field.type}
                required={field.required}
                value={values[field.id] ?? ''}
                placeholder={field.placeholder}
                onChange={(event) => updateValue(field.id, event.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-xs text-slate-100 outline-none ring-0 transition focus:border-sky-500"
              />
            )}
          </label>
        ))}
      </div>
      <div className="mt-3">
        <ActionButton label={submitLabel} variant="primary" onClick={submit} />
      </div>
    </div>
  );
}
