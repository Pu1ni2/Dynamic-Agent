import { useState, type KeyboardEvent } from "react";
import { motion } from "framer-motion";

interface Props {
  onSubmit: (task: string) => void;
}

export function InputScreen({ onSubmit }: Props) {
  const [task, setTask] = useState("");

  const handleSubmit = () => {
    if (task.trim()) onSubmit(task.trim());
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit();
  };

  return (
    <div className="min-h-screen bg-bg flex flex-col items-center justify-center px-6">
      {/* Grid background */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(249,115,22,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(249,115,22,0.03) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative w-full max-w-2xl"
      >
        {/* Logo */}
        <div className="text-center mb-12">
          <motion.h1
            className="text-5xl font-bold tracking-tight text-white"
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            Hive<span className="text-accent">Mind</span>
          </motion.h1>
          <motion.p
            className="mt-3 text-muted text-base"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25 }}
          >
            Dynamic multi-agent orchestration with shared memory
          </motion.p>
        </div>

        {/* Input card */}
        <motion.div
          className="rounded-2xl border border-border bg-card p-6"
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          style={{ boxShadow: "0 0 48px rgba(249,115,22,0.08)" }}
        >
          <label className="block text-sm font-medium text-muted mb-3">
            What do you want HiveMind to solve?
          </label>
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            onKeyDown={handleKey}
            placeholder="e.g. Plan our Q3 product launch including marketing, hiring, budget, and legal review"
            rows={4}
            className="w-full bg-surface text-white placeholder-faint rounded-xl border border-border px-4 py-3 text-sm resize-none outline-none transition-all duration-200 focus:border-accent"
            style={{
              boxShadow: task ? "0 0 0 1px #F97316, 0 0 20px rgba(249,115,22,0.15)" : undefined,
            }}
          />
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-faint">⌘ + Enter to submit</span>
            <button
              onClick={handleSubmit}
              disabled={!task.trim()}
              className="px-6 py-2.5 rounded-xl bg-accent text-white text-sm font-semibold transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed hover:bg-accent-dark hover:shadow-glow active:scale-95"
            >
              Launch Pipeline →
            </button>
          </div>
        </motion.div>

        {/* Example prompts */}
        <motion.div
          className="mt-6 flex flex-wrap gap-2 justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          {[
            "Analyze our competitors and recommend positioning strategy",
            "Plan a company offsite for 50 people",
            "Design a microservices migration roadmap",
          ].map((example) => (
            <button
              key={example}
              onClick={() => setTask(example)}
              className="text-xs text-faint border border-border rounded-full px-3 py-1.5 hover:border-accent hover:text-accent transition-all duration-150"
            >
              {example}
            </button>
          ))}
        </motion.div>
      </motion.div>
    </div>
  );
}
