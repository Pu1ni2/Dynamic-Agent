import { motion } from "framer-motion";
import { usePipelineStore } from "../store/pipelineStore";
import { StatusRing } from "./StatusRing";
import type { AgentStatus } from "../types";

const tierColors: Record<string, string> = {
  FAST: "text-green-400 bg-green-400/10 border-green-400/20",
  BALANCED: "text-accent bg-accent/10 border-accent/20",
  HEAVY: "text-orange-300 bg-orange-300/10 border-orange-300/20",
};

export function AgentGrid() {
  const spawnedAgents = usePipelineStore((s) => s.spawnedAgents);
  const agentStatuses = usePipelineStore((s) => s.agentStatuses);
  const agentOutputs = usePipelineStore((s) => s.agentOutputs);

  const containerVariants = {
    hidden: {},
    visible: { transition: { staggerChildren: 0.08 } },
  };

  const cardVariants = {
    hidden: { opacity: 0, scale: 0.85, y: 20 },
    visible: { opacity: 1, scale: 1, y: 0, transition: { type: "spring" as const, stiffness: 260, damping: 20 } },
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white">Parallel Execution</h2>
          <p className="text-xs text-muted mt-0.5">
            {spawnedAgents.length} sub-agents running concurrently
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-faint" /> idle
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-accent animate-pulse" /> running
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-accent" /> done
          </span>
        </div>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid gap-4"
        style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}
      >
        {spawnedAgents.map((agent) => {
          const status: AgentStatus = agentStatuses[agent.id] || "idle";
          const output = agentOutputs[agent.id];
          const tierClass = tierColors[agent.model_tier] || tierColors.BALANCED;

          return (
            <motion.div
              key={agent.id}
              variants={cardVariants}
              className={`rounded-2xl border bg-card p-4 flex flex-col gap-3 transition-all duration-300 ${
                status === "running"
                  ? "border-accent/50 shadow-glow-sm"
                  : status === "done"
                  ? "border-accent/30"
                  : "border-border"
              }`}
            >
              {/* Header */}
              <div className="flex items-center gap-3">
                <StatusRing status={status} size={44} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white truncate">{agent.role}</p>
                  <span className={`inline-block mt-0.5 text-xs px-2 py-0.5 rounded-full border font-medium ${tierClass}`}>
                    {agent.model_tier}
                  </span>
                </div>
              </div>

              {/* Output preview */}
              <div className="min-h-[48px]">
                {status === "running" && (
                  <p className="text-xs text-faint animate-pulse">Processing...</p>
                )}
                {status === "done" && output && (
                  <p className="text-xs text-muted line-clamp-4 leading-relaxed">{output.slice(0, 200)}</p>
                )}
                {status === "idle" && (
                  <p className="text-xs text-faint">Queued</p>
                )}
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
