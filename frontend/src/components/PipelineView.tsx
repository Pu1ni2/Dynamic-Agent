import { motion, AnimatePresence } from "framer-motion";
import { usePipelineStore } from "../store/pipelineStore";
import { DebatePanel } from "./DebatePanel";
import { AgentGrid } from "./AgentGrid";
import { AssemblyView } from "./AssemblyView";
import type { PhaseId } from "../types";

const PHASES: { id: PhaseId; label: string; step: number }[] = [
  { id: "debate_requirements", label: "Requirements", step: 1 },
  { id: "debate_plan", label: "Plan Debate", step: 2 },
  { id: "execution", label: "Execution", step: 3 },
  { id: "assembly", label: "Assembly", step: 4 },
];

function PhaseBar({ current }: { current: PhaseId | null }) {
  const currentStep = PHASES.find((p) => p.id === current)?.step ?? 0;

  return (
    <div className="flex items-center gap-0 mb-10">
      {PHASES.map((phase, i) => {
        const done = currentStep > phase.step;
        const active = currentStep === phase.step;

        return (
          <div key={phase.id} className="flex items-center flex-1">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                  done
                    ? "bg-accent text-white"
                    : active
                    ? "bg-accent/20 border-2 border-accent text-accent"
                    : "bg-surface border border-border text-faint"
                }`}
              >
                {done ? "✓" : phase.step}
              </div>
              <span className={`text-xs transition-colors ${active ? "text-accent" : done ? "text-muted" : "text-faint"}`}>
                {phase.label}
              </span>
            </div>
            {i < PHASES.length - 1 && (
              <div
                className="flex-1 h-px mx-2 mb-5 transition-all duration-500"
                style={{ background: done ? "#F97316" : "#27272A" }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export function PipelineView() {
  const phase = usePipelineStore((s) => s.phase);
  const status = usePipelineStore((s) => s.status);
  const error = usePipelineStore((s) => s.error);

  return (
    <div className="min-h-screen bg-bg">
      {/* Grid background */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(249,115,22,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(249,115,22,0.03) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />

      <div className="relative max-w-5xl mx-auto px-6 py-8">
        {/* Top bar */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-white">
            Hive<span className="text-accent">Mind</span>
          </h1>
          <div className="flex items-center gap-2">
            {status === "running" && (
              <span className="flex items-center gap-2 text-xs text-accent">
                <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                Pipeline running
              </span>
            )}
            {status === "done" && (
              <span className="flex items-center gap-2 text-xs text-muted">
                <span className="w-2 h-2 rounded-full bg-accent" />
                Complete
              </span>
            )}
          </div>
        </div>

        {/* Phase progress bar */}
        <PhaseBar current={phase} />

        {/* Error state */}
        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 mb-6">
            <p className="text-sm text-red-400 font-medium">Pipeline error</p>
            <p className="text-xs text-red-300/70 mt-1">{error}</p>
          </div>
        )}

        {/* Phase content */}
        <AnimatePresence mode="wait">
          {phase && (
            <motion.div
              key={phase}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              {phase === "debate_requirements" && <DebatePanel phase="requirements" />}
              {phase === "debate_plan" && <DebatePanel phase="plan" />}
              {phase === "execution" && <AgentGrid />}
              {phase === "assembly" && <AssemblyView />}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Waiting state */}
        {!phase && !error && (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-10 h-10 rounded-full border-2 border-accent/30 border-t-accent animate-spin" />
            <p className="text-sm text-muted">Initialising pipeline...</p>
          </div>
        )}
      </div>
    </div>
  );
}
