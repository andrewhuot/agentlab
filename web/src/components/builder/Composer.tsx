import { useMemo, useState } from 'react';
import { Paperclip, SendHorizonal } from 'lucide-react';
import type { ExecutionMode } from '../../lib/builder-types';
import { ActionButton, ModeSelector, SlashCommandMenu } from './widgets';

interface ComposerProps {
  mode: ExecutionMode;
  value: string;
  disabled?: boolean;
  onModeChange: (mode: ExecutionMode) => void;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function Composer({ mode, value, disabled = false, onModeChange, onChange, onSubmit }: ComposerProps) {
  const [attachments, setAttachments] = useState<string[]>([]);
  const [slashVisible, setSlashVisible] = useState(false);

  const slashQuery = useMemo(() => {
    const trimmed = value.trim();
    if (!trimmed.startsWith('/')) return '';
    return trimmed;
  }, [value]);

  const addAttachment = () => {
    setAttachments((prev) => [...prev, `attachment-${prev.length + 1}`]);
  };

  const removeAttachment = (name: string) => {
    setAttachments((prev) => prev.filter((item) => item !== name));
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      onSubmit();
    }

    if (event.key === '/') {
      setSlashVisible(true);
    }
  };

  return (
    <div className="relative border-t border-slate-800 bg-slate-950 px-3 py-3">
      <SlashCommandMenu
        visible={slashVisible}
        query={slashQuery}
        onSelect={(command) => {
          onChange(command);
          setSlashVisible(false);
        }}
      />

      <div className="mb-2 flex items-center gap-2">
        <ModeSelector value={mode} onChange={onModeChange} />
        <ActionButton
          label="Attach"
          icon={<Paperclip className="h-3.5 w-3.5" />}
          onClick={addAttachment}
        />
      </div>

      {attachments.length > 0 ? (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {attachments.map((attachment) => (
            <button
              key={attachment}
              type="button"
              onClick={() => removeAttachment(attachment)}
              className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-[11px] text-slate-400"
            >
              {attachment} ×
            </button>
          ))}
        </div>
      ) : null}

      <div className="flex items-end gap-2">
        <textarea
          value={value}
          disabled={disabled}
          onKeyDown={onKeyDown}
          onChange={(event) => {
            onChange(event.target.value);
            if (!event.target.value.startsWith('/')) {
              setSlashVisible(false);
            }
          }}
          placeholder="Ask for a plan, run traces, or apply a patch…"
          className="min-h-[70px] flex-1 resize-none rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none transition focus:border-sky-500"
        />
        <button
          type="button"
          disabled={disabled || value.trim().length === 0}
          onClick={onSubmit}
          className="rounded-lg bg-sky-500 p-2 text-white transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <SendHorizonal className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
