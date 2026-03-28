import type { ReactNode } from 'react';
import {
  Bell,
  ChevronLeft,
  ChevronRight,
  FolderTree,
  MessageSquare,
  ListTodo,
  Star,
} from 'lucide-react';
import type { BuilderProject, BuilderSession, BuilderTask } from '../../lib/builder-types';
import { classNames } from '../../lib/utils';

export interface RailFavorite {
  id: string;
  label: string;
  kind: 'project' | 'session' | 'task';
}

export interface RailNotification {
  id: string;
  message: string;
  severity: 'info' | 'warning' | 'error';
}

interface LeftRailProps {
  collapsed: boolean;
  projects: BuilderProject[];
  sessions: BuilderSession[];
  tasks: BuilderTask[];
  selectedProjectId: string | null;
  selectedSessionId: string | null;
  selectedTaskId: string | null;
  favorites?: RailFavorite[];
  notifications?: RailNotification[];
  onToggle: () => void;
  onSelectProject: (projectId: string) => void;
  onSelectSession: (sessionId: string) => void;
  onSelectTask: (taskId: string) => void;
}

export function LeftRail({
  collapsed,
  projects,
  sessions,
  tasks,
  selectedProjectId,
  selectedSessionId,
  selectedTaskId,
  favorites = [],
  notifications = [],
  onToggle,
  onSelectProject,
  onSelectSession,
  onSelectTask,
}: LeftRailProps) {
  const width = collapsed ? 56 : 260;

  return (
    <aside
      className="flex h-full flex-col border-r border-slate-800 bg-slate-950 transition-all"
      style={{ width, minWidth: width, maxWidth: width }}
    >
      <div className="flex h-12 items-center justify-between border-b border-slate-800 px-2.5">
        {!collapsed ? <p className="text-xs font-semibold text-slate-400">Workspace</p> : null}
        <button
          type="button"
          onClick={onToggle}
          className="rounded p-1.5 text-slate-500 transition hover:bg-slate-800 hover:text-slate-200"
          aria-label={collapsed ? 'Expand panel' : 'Collapse panel'}
        >
          {collapsed ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 py-2">
        {!collapsed ? (
          <SectionTitle icon={<FolderTree className="h-3.5 w-3.5" />} title="Projects" />
        ) : null}
        {projects.map((project) => (
          <Row
            key={project.project_id}
            compact={collapsed}
            selected={project.project_id === selectedProjectId}
            label={project.name}
            onClick={() => onSelectProject(project.project_id)}
          />
        ))}

        {!collapsed ? (
          <SectionTitle icon={<MessageSquare className="mt-3 h-3.5 w-3.5" />} title="Sessions" />
        ) : null}
        {sessions.map((session) => (
          <Row
            key={session.session_id}
            compact={collapsed}
            selected={session.session_id === selectedSessionId}
            label={session.title || 'Untitled session'}
            subLabel={session.status}
            onClick={() => onSelectSession(session.session_id)}
          />
        ))}

        {!collapsed ? <SectionTitle icon={<ListTodo className="mt-3 h-3.5 w-3.5" />} title="Tasks" /> : null}
        {tasks.map((task) => (
          <Row
            key={task.task_id}
            compact={collapsed}
            selected={task.task_id === selectedTaskId}
            label={task.title || 'Untitled task'}
            subLabel={task.status}
            onClick={() => onSelectTask(task.task_id)}
          />
        ))}

        {!collapsed ? <SectionTitle icon={<Star className="mt-3 h-3.5 w-3.5" />} title="Favorites" /> : null}
        {favorites.length === 0 && !collapsed ? (
          <p className="mb-1 rounded border border-slate-800 bg-slate-900/50 px-2 py-1.5 text-[11px] text-slate-500">
            Pin key projects or tasks.
          </p>
        ) : null}
        {favorites.map((favorite) => (
          <Row
            key={favorite.id}
            compact={collapsed}
            selected={false}
            label={favorite.label}
            subLabel={favorite.kind}
            onClick={() => {
              if (favorite.kind === 'project') onSelectProject(favorite.id);
              if (favorite.kind === 'session') onSelectSession(favorite.id);
              if (favorite.kind === 'task') onSelectTask(favorite.id);
            }}
          />
        ))}

        {!collapsed ? (
          <SectionTitle icon={<Bell className="mt-3 h-3.5 w-3.5" />} title="Notifications" />
        ) : null}
        {notifications.length === 0 && !collapsed ? (
          <p className="rounded border border-slate-800 bg-slate-900/50 px-2 py-1.5 text-[11px] text-slate-500">
            No notifications.
          </p>
        ) : null}
        {notifications.map((notification) => {
          const tone =
            notification.severity === 'error'
              ? 'text-rose-300 border-rose-700/40 bg-rose-500/10'
              : notification.severity === 'warning'
                ? 'text-amber-300 border-amber-700/40 bg-amber-500/10'
                : 'text-slate-300 border-slate-700 bg-slate-900/60';
          return (
            <p
              key={notification.id}
              className={classNames(
                'mb-1 rounded border px-2 py-1.5 text-[11px]',
                tone,
                collapsed && 'text-center'
              )}
              title={notification.message}
            >
              {collapsed ? '•' : notification.message}
            </p>
          );
        })}
      </div>
    </aside>
  );
}

function SectionTitle({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="mb-1 mt-2 flex items-center gap-1.5 px-1 text-[11px] uppercase tracking-wide text-slate-500">
      {icon}
      <span>{title}</span>
    </div>
  );
}

function Row({
  compact,
  selected,
  label,
  subLabel,
  onClick,
}: {
  compact: boolean;
  selected: boolean;
  label: string;
  subLabel?: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={classNames(
        'mb-1 w-full rounded-md border px-2 py-1.5 text-left transition',
        selected
          ? 'border-sky-500/60 bg-sky-500/10 text-slate-100'
          : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700 hover:text-slate-200'
      )}
    >
      {compact ? (
        <span className="block truncate text-[11px]">{label.slice(0, 1).toUpperCase()}</span>
      ) : (
        <>
          <span className="block truncate text-xs">{label}</span>
          {subLabel ? <span className="block text-[11px] text-slate-500">{subLabel}</span> : null}
        </>
      )}
    </button>
  );
}
