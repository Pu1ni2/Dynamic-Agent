import { useCallback, useRef } from "react";
import { usePipelineStore } from "../store/pipelineStore";
import type { PipelineEvent } from "../types";

export function usePipelineSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const handleEvent = usePipelineStore((s) => s.handleEvent);
  const reset = usePipelineStore((s) => s.reset);

  const submit = useCallback(
    (task: string) => {
      reset();

      const ws = new WebSocket(`ws://${window.location.hostname}:8000/ws/pipeline`);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({ task }));
      };

      ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data) as PipelineEvent;
          handleEvent(event);
        } catch {
          // ignore malformed messages
        }
      };

      ws.onerror = () => {
        handleEvent({ type: "error", message: "WebSocket connection failed. Is the server running?" });
      };

      ws.onclose = () => {
        wsRef.current = null;
      };
    },
    [handleEvent, reset]
  );

  return { submit };
}
