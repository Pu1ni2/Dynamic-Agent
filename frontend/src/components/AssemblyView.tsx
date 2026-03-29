import { motion, AnimatePresence } from "framer-motion";
import { usePipelineStore } from "../store/pipelineStore";

export function AssemblyView() {
  const finalOutput = usePipelineStore((s) => s.finalOutput);
  const knownIssues = usePipelineStore((s) => s.knownIssues);
  const agentOutputs = usePipelineStore((s) => s.agentOutputs);
  const spawnedAgents = usePipelineStore((s) => s.spawnedAgents);

  return (
    <div className="w-full max-w-5xl mx-auto">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white">Final Assembly</h2>
        <p className="text-xs text-muted mt-0.5">DA synthesising all agent outputs</p>
      </div>

      {/* Mini agent summary strip */}
      <div className="flex flex-wrap gap-2 mb-6">
        {spawnedAgents.map((agent) => (
          <motion.span
            key={agent.id}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface border border-border text-xs text-muted"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-accent" />
            {agent.role}
          </motion.span>
        ))}
        <motion.span
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-accent/10 border border-accent/30 text-xs text-accent"
        >
          → DA Assembles
        </motion.span>
      </div>

      <AnimatePresence>
        {finalOutput ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.45 }}
            className="rounded-2xl border border-accent/30 bg-card p-6"
            style={{ boxShadow: "0 0 48px rgba(249,115,22,0.12)" }}
          >
            <div className="flex items-center gap-2.5 mb-5 pb-4 border-b border-border">
              <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center text-sm text-accent">⬡</div>
              <div>
                <p className="text-sm font-semibold text-white">HiveMind Output</p>
                <p className="text-xs text-faint">Synthesised from {spawnedAgents.length} agents</p>
              </div>
              <span
                className="ml-auto px-3 py-1 rounded-full text-xs font-semibold bg-accent text-white"
                style={{ boxShadow: "0 0 12px rgba(249,115,22,0.4)" }}
              >
                Complete
              </span>
            </div>

            <div className="prose prose-invert prose-sm max-w-none">
              <pre className="text-sm text-white/90 whitespace-pre-wrap font-sans leading-relaxed bg-transparent p-0 m-0">
                {finalOutput}
              </pre>
            </div>

            {knownIssues.length > 0 && (
              <div className="mt-5 pt-4 border-t border-border">
                <p className="text-xs font-medium text-muted mb-2">Known Issues / Caveats</p>
                <ul className="space-y-1">
                  {knownIssues.map((issue, i) => (
                    <li key={i} className="text-xs text-faint flex items-start gap-1.5">
                      <span className="text-accent mt-0.5">·</span>
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div
            className="rounded-2xl border border-border bg-card p-8 flex flex-col items-center justify-center gap-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="w-10 h-10 rounded-full border-2 border-accent/40 border-t-accent animate-spin" />
            <p className="text-sm text-muted">Compiling final output...</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Per-agent expandable outputs */}
      {finalOutput && Object.keys(agentOutputs).length > 0 && (
        <motion.details
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-4 rounded-xl border border-border bg-surface"
        >
          <summary className="px-4 py-3 text-xs text-muted cursor-pointer hover:text-white transition-colors select-none">
            View individual agent outputs ({Object.keys(agentOutputs).length} agents)
          </summary>
          <div className="px-4 pb-4 space-y-3">
            {spawnedAgents.map((agent) => {
              const out = agentOutputs[agent.id];
              if (!out) return null;
              return (
                <div key={agent.id} className="rounded-xl border border-border bg-card p-3">
                  <p className="text-xs font-semibold text-accent mb-2">{agent.role}</p>
                  <p className="text-xs text-muted font-mono whitespace-pre-wrap leading-relaxed">{out}</p>
                </div>
              );
            })}
          </div>
        </motion.details>
      )}
    </div>
  );
}
