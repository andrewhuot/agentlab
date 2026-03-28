import { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type SpotlightRegion = 'left_rail' | 'conversation' | 'inspector' | 'composer' | 'topbar' | 'none';

export interface DemoStep {
  id: string;
  region: SpotlightRegion;
  title: string;
  body: string;
  /** Optional CSS selector to highlight a specific element within the region */
  selector?: string;
  /** Auto-advance after this many milliseconds. Undefined = manual only. */
  autoAdvanceMs?: number;
}

interface DemoOverlayProps {
  steps: DemoStep[];
  currentStep: number;
  visible: boolean;
  /** Total acts count for the outer progress bar */
  actNumber?: number;
  actTotal?: number;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// Region bounding boxes (approximate — relative to viewport)
// These are matched against a data-builder-region attribute on the layout.
// ---------------------------------------------------------------------------

function getRegionRect(region: SpotlightRegion): DOMRect | null {
  if (region === 'none') return null;
  const el = document.querySelector(`[data-builder-region="${region}"]`);
  if (el) return el.getBoundingClientRect();
  return null;
}

// Padding around the spotlight cutout
const PADDING = 8;

interface Cutout {
  top: number;
  left: number;
  width: number;
  height: number;
}

function rectToCutout(rect: DOMRect): Cutout {
  return {
    top: rect.top - PADDING,
    left: rect.left - PADDING,
    width: rect.width + PADDING * 2,
    height: rect.height + PADDING * 2,
  };
}

// ---------------------------------------------------------------------------
// Tooltip position strategy
// ---------------------------------------------------------------------------

type TooltipSide = 'bottom' | 'top' | 'right' | 'left';

function chooseTooltipSide(cutout: Cutout): TooltipSide {
  const vh = window.innerHeight;
  const vw = window.innerWidth;
  const spaceBelow = vh - (cutout.top + cutout.height);
  const spaceRight = vw - (cutout.left + cutout.width);
  if (spaceBelow >= 200) return 'bottom';
  if (spaceRight >= 320) return 'right';
  if (cutout.top >= 200) return 'top';
  return 'left';
}

interface TooltipPos {
  top?: number | string;
  bottom?: number | string;
  left?: number | string;
  right?: number | string;
  transform?: string;
}

function computeTooltipPos(cutout: Cutout, side: TooltipSide): TooltipPos {
  const TOOLTIP_W = 320;
  const TOOLTIP_OFFSET = 16;
  switch (side) {
    case 'bottom':
      return {
        top: cutout.top + cutout.height + TOOLTIP_OFFSET,
        left: Math.max(16, Math.min(cutout.left, window.innerWidth - TOOLTIP_W - 16)),
      };
    case 'top':
      return {
        top: cutout.top - TOOLTIP_OFFSET,
        left: Math.max(16, Math.min(cutout.left, window.innerWidth - TOOLTIP_W - 16)),
        transform: 'translateY(-100%)',
      };
    case 'right':
      return {
        top: Math.max(16, cutout.top),
        left: cutout.left + cutout.width + TOOLTIP_OFFSET,
      };
    case 'left':
      return {
        top: Math.max(16, cutout.top),
        left: cutout.left - TOOLTIP_W - TOOLTIP_OFFSET,
      };
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function DemoOverlay({
  steps,
  currentStep,
  visible,
  actNumber,
  actTotal,
  onNext,
  onPrev,
  onSkip,
  onClose,
}: DemoOverlayProps) {
  const [cutout, setCutout] = useState<Cutout | null>(null);
  const [tooltipPos, setTooltipPos] = useState<TooltipPos>({});
  const autoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const step = steps[currentStep];

  const recalcLayout = useCallback(() => {
    if (!step || step.region === 'none') {
      setCutout(null);
      return;
    }
    const rect = getRegionRect(step.region);
    if (!rect) {
      setCutout(null);
      return;
    }
    const c = rectToCutout(rect);
    const side = chooseTooltipSide(c);
    setCutout(c);
    setTooltipPos(computeTooltipPos(c, side));
  }, [step]);

  useEffect(() => {
    if (!visible) return;
    recalcLayout();
    window.addEventListener('resize', recalcLayout);
    window.addEventListener('scroll', recalcLayout, true);
    return () => {
      window.removeEventListener('resize', recalcLayout);
      window.removeEventListener('scroll', recalcLayout, true);
    };
  }, [visible, recalcLayout]);

  // Auto-advance
  useEffect(() => {
    if (autoTimerRef.current) {
      clearTimeout(autoTimerRef.current);
    }
    if (visible && step?.autoAdvanceMs) {
      autoTimerRef.current = setTimeout(() => {
        onNext();
      }, step.autoAdvanceMs);
    }
    return () => {
      if (autoTimerRef.current) clearTimeout(autoTimerRef.current);
    };
  }, [visible, step, currentStep, onNext]);

  // Keyboard nav
  useEffect(() => {
    if (!visible) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'Enter') onNext();
      else if (e.key === 'ArrowLeft') onPrev();
      else if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [visible, onNext, onPrev, onClose]);

  if (!visible || !step) return null;

  const isFirst = currentStep === 0;
  const isLast = currentStep === steps.length - 1;

  // Build SVG clip path for the cutout effect
  const vh = typeof window !== 'undefined' ? window.innerHeight : 900;
  const vw = typeof window !== 'undefined' ? window.innerWidth : 1440;

  const clipPath = cutout
    ? `M0,0 H${vw} V${vh} H0 Z M${cutout.left},${cutout.top} H${cutout.left + cutout.width} V${cutout.top + cutout.height} H${cutout.left} Z`
    : undefined;

  return (
    <>
      {/* Dimmed backdrop with cutout */}
      <div
        className="pointer-events-none fixed inset-0 z-[100]"
        style={{ isolation: 'isolate' }}
      >
        {cutout ? (
          <svg
            className="absolute inset-0 h-full w-full"
            style={{ pointerEvents: 'none' }}
          >
            <defs>
              <clipPath id="demo-cutout-clip" clipRule="evenodd">
                <path
                  fillRule="evenodd"
                  d={clipPath}
                />
              </clipPath>
            </defs>
            <rect
              x="0"
              y="0"
              width={vw}
              height={vh}
              fill="rgba(0,0,0,0.65)"
              clipPath="url(#demo-cutout-clip)"
            />
          </svg>
        ) : (
          <div className="absolute inset-0 bg-black/65" />
        )}
      </div>

      {/* Spotlight border ring */}
      {cutout && (
        <div
          className="pointer-events-none fixed z-[101] rounded-xl ring-2 ring-violet-400/60 ring-offset-0 transition-all duration-300"
          style={{
            top: cutout.top,
            left: cutout.left,
            width: cutout.width,
            height: cutout.height,
            boxShadow: '0 0 0 2px rgba(139,92,246,0.3), 0 0 24px rgba(139,92,246,0.2)',
          }}
        />
      )}

      {/* Tooltip card */}
      <div
        className="fixed z-[102] w-80 rounded-2xl border border-white/10 bg-slate-900 shadow-2xl shadow-black/60 transition-all duration-200"
        style={{
          ...tooltipPos,
          ...(cutout ? {} : { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }),
        }}
      >
        {/* Top bar */}
        <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
          <div className="flex items-center gap-2">
            {actNumber !== undefined && actTotal !== undefined && (
              <span className="rounded-md bg-violet-500/20 px-2 py-0.5 text-[10px] font-semibold text-violet-300">
                Act {actNumber}/{actTotal}
              </span>
            )}
            <span className="text-[11px] text-slate-500">
              Step {currentStep + 1} of {steps.length}
            </span>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-slate-500 transition-colors hover:bg-white/5 hover:text-slate-300"
            aria-label="Close demo overlay"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Step progress bar */}
        <div className="h-0.5 bg-slate-800">
          <div
            className="h-full bg-gradient-to-r from-violet-500 to-purple-500 transition-all duration-300"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>

        {/* Content */}
        <div className="px-4 py-4">
          <h4 className="text-sm font-semibold text-white">{step.title}</h4>
          <p className="mt-2 text-[13px] leading-relaxed text-slate-400">{step.body}</p>
        </div>

        {/* Auto-advance indicator */}
        {step.autoAdvanceMs && (
          <div className="px-4 pb-2">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
              <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-400" />
              Auto-advancing in {Math.round(step.autoAdvanceMs / 1000)}s
            </div>
          </div>
        )}

        {/* Navigation footer */}
        <div className="flex items-center justify-between border-t border-white/5 px-4 py-3">
          <button
            onClick={onSkip}
            className="text-[12px] text-slate-500 transition-colors hover:text-slate-300"
          >
            Skip demo
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onPrev}
              disabled={isFirst}
              className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-white/10 text-slate-400 transition-all hover:border-white/20 hover:bg-white/5 hover:text-white disabled:opacity-30"
              aria-label="Previous step"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={isLast ? onClose : onNext}
              className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-violet-600 to-purple-600 px-3 py-1.5 text-xs font-semibold text-white shadow-md transition-all hover:from-violet-500 hover:to-purple-500"
            >
              {isLast ? 'Done' : 'Next'}
              {!isLast && <ChevronRight className="h-3.5 w-3.5" />}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------------------
// useDemoOverlay — convenience hook for managing overlay state
// ---------------------------------------------------------------------------

export interface UseDemoOverlayReturn {
  visible: boolean;
  currentStep: number;
  start: () => void;
  next: () => void;
  prev: () => void;
  skip: () => void;
  close: () => void;
  goTo: (index: number) => void;
}

export function useDemoOverlay(steps: DemoStep[]): UseDemoOverlayReturn {
  const [visible, setVisible] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  const start = useCallback(() => {
    setCurrentStep(0);
    setVisible(true);
  }, []);

  const next = useCallback(() => {
    setCurrentStep((i) => Math.min(i + 1, steps.length - 1));
  }, [steps.length]);

  const prev = useCallback(() => {
    setCurrentStep((i) => Math.max(i - 1, 0));
  }, []);

  const skip = useCallback(() => {
    setCurrentStep(steps.length - 1);
  }, [steps.length]);

  const close = useCallback(() => {
    setVisible(false);
    setCurrentStep(0);
  }, []);

  const goTo = useCallback((index: number) => {
    setCurrentStep(Math.max(0, Math.min(index, steps.length - 1)));
  }, [steps.length]);

  return { visible, currentStep, start, next, prev, skip, close, goTo };
}

// ---------------------------------------------------------------------------
// Pre-built step sets for each demo act
// ---------------------------------------------------------------------------

export const ACT_1_STEPS: DemoStep[] = [
  {
    id: 'act1-welcome',
    region: 'conversation',
    title: 'Start with a conversation',
    body: 'Every agent starts here. Type what you want to build in plain language — no YAML, no config files. The orchestrator reads your intent and assembles a specialist team.',
  },
  {
    id: 'act1-left-rail',
    region: 'left_rail',
    title: 'Your project structure',
    body: 'The left rail shows your project, sessions, and task tree. The requirements analyst will create the first session automatically after you submit your request.',
  },
  {
    id: 'act1-plan-card',
    region: 'conversation',
    title: 'Plan card appears',
    body: 'The requirements analyst outputs a structured Plan card with goals, constraints, and milestones. Review it, revise it, or approve it — the architect is waiting.',
  },
  {
    id: 'act1-composer',
    region: 'composer',
    title: 'Choose your execution mode',
    body: 'Draft mode proposes before writing. Apply mode executes directly. Delegate mode runs autonomously in a sandboxed worktree. Start in Draft to stay in control.',
  },
];

export const ACT_2_STEPS: DemoStep[] = [
  {
    id: 'act2-tools-tab',
    region: 'inspector',
    title: 'Inspector: Tools tab',
    body: 'The Inspector shows every tool, skill, and guardrail in your agent. Watch as the tool engineer scaffolds Sabre GDS integration — each change is a source diff you can inspect.',
  },
  {
    id: 'act2-diff-card',
    region: 'conversation',
    title: 'Source diff cards',
    body: 'Every file change appears as a diff card in the conversation. Approve it to merge into the agent, or ask for revisions. No surprises in the codebase.',
  },
  {
    id: 'act2-skill-card',
    region: 'conversation',
    title: 'Skill cards',
    body: 'The skill author chains tools into multi-step skills — like the rebooking flow that verifies identity, checks alternatives, and confirms with the passenger.',
  },
  {
    id: 'act2-guardrails-tab',
    region: 'inspector',
    title: 'Inspector: Guardrails tab',
    body: 'Guardrails are first-class citizens. The PII filter masks credit card numbers and passport IDs before any log write. View enforcement rate, patterns, and test coverage here.',
  },
];

export const ACT_3_STEPS: DemoStep[] = [
  {
    id: 'act3-evals-tab',
    region: 'inspector',
    title: 'Inspector: Eval Results',
    body: '120 conversations run. Trajectory quality: 0.61. Hard gate threshold: 0.80. The failure breakdown shows 23 failures from a seat_inventory schema bug.',
  },
  {
    id: 'act3-trace-viewer',
    region: 'inspector',
    title: 'Trace viewer',
    body: 'Drill into the failing trace. The trace analyst has bookmarked the root-cause span: seat_inventory_tool._build_response() returns a flat list instead of a seat_map dict.',
  },
  {
    id: 'act3-trace-card',
    region: 'conversation',
    title: 'Trace evidence cards',
    body: 'Bookmarked traces appear as evidence cards in the conversation. The analyst has already promoted the failure to an eval case — it will block future regressions.',
  },
];

export const ACT_4_STEPS: DemoStep[] = [
  {
    id: 'act4-proposal',
    region: 'conversation',
    title: 'Targeted fix proposal',
    body: 'The tool engineer proposes a surgical fix: wrap the seat list in a {seat_map} envelope, add pydantic validation, add a unit test. 12 lines changed.',
  },
  {
    id: 'act4-approval',
    region: 'conversation',
    title: 'Source write approval',
    body: 'Before any file is written, you see an approval request. Approve once, for this task — or grant project-wide if you trust the engineer. Reject to go back to drafts.',
  },
  {
    id: 'act4-diff',
    region: 'inspector',
    title: 'Diff viewer',
    body: 'Inspect the exact changes: the new SeatInventoryResponse pydantic model, the wrapper, the unit test. Nothing merged without your eyes on it.',
  },
  {
    id: 'act4-eval-after',
    region: 'inspector',
    title: 'Eval results: before vs after',
    body: 'Re-run after the fix: trajectory quality 0.61 → 0.84. Hard gate PASSED. The eval bundle shows the delta and the specific tests that flipped from fail to pass.',
  },
];

export const ACT_5_STEPS: DemoStep[] = [
  {
    id: 'act5-release-card',
    region: 'conversation',
    title: 'Release candidate card',
    body: 'RC v1.0.0 bundles every approved artifact: the graph diff, tools, skills, guardrails. The changelog is generated from task history. Eval score attached.',
  },
  {
    id: 'act5-deployment-approval',
    region: 'conversation',
    title: 'Deployment approval',
    body: 'The final gate: a deployment approval request for gcp-us-central1-prod. See the eval scores, rollback plan, and affected user count before you sign off.',
  },
  {
    id: 'act5-inspector-release',
    region: 'inspector',
    title: 'Release panel',
    body: 'The Inspector shows the full release manifest — artifact IDs, eval bundle, deployment target, and provenance chain. Every decision is auditable.',
  },
];

export const ALL_ACT_STEPS: Record<string, DemoStep[]> = {
  act1_build: ACT_1_STEPS,
  act2_develop: ACT_2_STEPS,
  act3_evaluate: ACT_3_STEPS,
  act4_optimize: ACT_4_STEPS,
  act5_ship: ACT_5_STEPS,
};
