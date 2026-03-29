import { motion, AnimatePresence } from "framer-motion";

interface Props {
  round: number;
  maxRounds?: number;
  approved?: boolean;
}

export function RoundBadge({ round, maxRounds = 3, approved }: Props) {
  return (
    <div className="flex items-center gap-2">
      <AnimatePresence mode="wait">
        {approved ? (
          <motion.span
            key="approved"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-accent text-white"
            style={{ boxShadow: "0 0 12px rgba(249,115,22,0.4)" }}
          >
            <span>✓</span> APPROVED
          </motion.span>
        ) : round > 0 ? (
          <motion.span
            key={`round-${round}`}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-surface border border-border text-muted"
          >
            Round {round} / {maxRounds}
          </motion.span>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
