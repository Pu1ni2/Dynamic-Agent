import { motion, AnimatePresence } from "framer-motion";
import { usePipelineStore } from "../store/pipelineStore";
import { RoundBadge } from "./RoundBadge";
import type { DebateMessage } from "../types";

interface Props {
  phase: "requirements" | "plan";
}

function MessageBubble({ msg }: { msg: DebateMessage }) {
  const isDA = msg.speaker === "DA";
  let preview = msg.content;
  try {
    const parsed = JSON.parse(msg.content);
    // Show a human-readable preview
    if (isDA) {
      preview = parsed.requirements?.objective || parsed.plan?.map((p: {role:string}) => p.role).join(", ") || msg.content.slice(0, 300);
    } else {
      preview = parsed.critique || (parsed.approved ? "✓ Plan looks solid." : "Needs revision.") || msg.content.slice(0, 300);
    }
  } catch {
    preview = msg.content.slice(0, 300);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl p-3 text-xs font-mono leading-relaxed border ${
        isDA
          ? "bg-surface border-border text-white"
          : msg.approved
          ? "bg-accent/10 border-accent/30 text-accent"
          : "bg-surface border-border-light text-muted"
      }`}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <span className={`font-semibold text-xs ${isDA ? "text-accent" : "text-muted"}`}>
          {isDA ? "Dynamic Agent" : "Evaluator"}
        </span>
        {!isDA && msg.approved && (
          <span className="text-accent text-xs">✓ Approved</span>
        )}
        {!isDA && !msg.approved && (
          <span className="text-faint text-xs">Rejected</span>
        )}
      </div>
      <p className="text-muted/90 whitespace-pre-wrap break-words line-clamp-6">{preview}</p>
    </motion.div>
  );
}

export function DebatePanel({ phase }: Props) {
  const debate = usePipelineStore((s) =>
    phase === "requirements" ? s.requirementsDebate : s.planDebate
  );

  const daMessages = debate.messages.filter((m) => m.speaker === "DA");
  const evalMessages = debate.messages.filter((m) => m.speaker === "Evaluator");
  const latestDA = daMessages[daMessages.length - 1];
  const latestEval = evalMessages[evalMessages.length - 1];

  return (
    <div className="w-full max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white">
            {phase === "requirements" ? "Requirements Debate" : "Plan Debate"}
          </h2>
          <p className="text-xs text-muted mt-0.5">
            {phase === "requirements"
              ? "DA proposes requirements · Evaluator critiques"
              : "DA designs sub-agent plan · Evaluator validates"}
          </p>
        </div>
        <RoundBadge round={debate.round} approved={debate.approved} />
      </div>

      {/* Two-column debate */}
      <div className="grid grid-cols-2 gap-4">
        {/* DA column */}
        <div className="rounded-2xl border border-border bg-card p-4 flex flex-col gap-3">
          <div className="flex items-center gap-2.5 pb-3 border-b border-border">
            <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center text-sm">⬡</div>
            <div>
              <p className="text-sm font-semibold text-white">Dynamic Agent</p>
              <p className="text-xs text-faint">Orchestrator · Plan Generator</p>
            </div>
            {debate.messages.some((m) => m.speaker === "DA") && (
              <span className="ml-auto w-2 h-2 rounded-full bg-accent animate-pulse" />
            )}
          </div>

          <div className="flex flex-col gap-2 min-h-[160px]">
            {latestDA ? (
              <MessageBubble msg={latestDA} />
            ) : (
              <div className="flex items-center justify-center h-full">
                <span className="text-faint text-xs animate-pulse">Generating proposal...</span>
              </div>
            )}
          </div>
        </div>

        {/* Evaluator column */}
        <div className="rounded-2xl border border-border bg-card p-4 flex flex-col gap-3">
          <div className="flex items-center gap-2.5 pb-3 border-b border-border">
            <div className="w-8 h-8 rounded-full bg-surface flex items-center justify-center text-sm border border-border">⚖</div>
            <div>
              <p className="text-sm font-semibold text-white">Evaluator</p>
              <p className="text-xs text-faint">Adversarial Reviewer</p>
            </div>
            {debate.messages.some((m) => m.speaker === "Evaluator") && (
              <span className="ml-auto w-2 h-2 rounded-full bg-faint" />
            )}
          </div>

          <div className="flex flex-col gap-2 min-h-[160px]">
            {latestEval ? (
              <MessageBubble msg={latestEval} />
            ) : (
              <div className="flex items-center justify-center h-full">
                <span className="text-faint text-xs">Waiting for proposal...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Approved banner */}
      <AnimatePresence>
        {debate.approved && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="mt-4 rounded-xl border border-accent/30 bg-accent/10 px-5 py-3 flex items-center gap-3"
            style={{ boxShadow: "0 0 24px rgba(249,115,22,0.15)" }}
          >
            <span className="text-accent text-lg">✓</span>
            <div>
              <p className="text-sm font-semibold text-accent">
                {phase === "requirements" ? "Requirements Approved" : "Plan Approved"}
              </p>
              <p className="text-xs text-muted mt-0.5">
                {phase === "requirements"
                  ? "Proceeding to sub-agent plan debate"
                  : "Spawning sub-agents from approved plan"}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
