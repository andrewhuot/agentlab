
interface Props {
  strategy: 'simple' | 'adaptive' | 'full';
}

const STRATEGY_STYLES = {
  simple: { bg: 'bg-zinc-800', text: 'text-zinc-300', label: 'Simple' },
  adaptive: { bg: 'bg-blue-950/50', text: 'text-blue-300', label: 'Adaptive' },
  full: { bg: 'bg-purple-950/50', text: 'text-purple-300', label: 'Full' },
};

export function SearchStrategyBadge({ strategy }: Props) {
  const style = STRATEGY_STYLES[strategy] || STRATEGY_STYLES.simple;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium ${style.bg} ${style.text}`}
    >
      {style.label}
    </span>
  );
}
