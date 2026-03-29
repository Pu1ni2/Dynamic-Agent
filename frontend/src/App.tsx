import { AnimatePresence, motion } from "framer-motion";
import { usePipelineStore } from "./store/pipelineStore";
import { usePipelineSocket } from "./hooks/usePipelineSocket";
import { InputScreen } from "./components/InputScreen";
import { PipelineView } from "./components/PipelineView";

export default function App() {
  const status = usePipelineStore((s) => s.status);
  const { submit } = usePipelineSocket();

  const showPipeline = status === "running" || status === "done" || status === "error";

  return (
    <AnimatePresence mode="wait">
      {!showPipeline ? (
        <motion.div key="input" exit={{ opacity: 0, scale: 0.97 }} transition={{ duration: 0.2 }}>
          <InputScreen onSubmit={submit} />
        </motion.div>
      ) : (
        <motion.div key="pipeline" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.3 }}>
          <PipelineView />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
