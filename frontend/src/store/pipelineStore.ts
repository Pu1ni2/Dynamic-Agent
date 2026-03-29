import { create } from "zustand";
import type { PhaseId, DebateState, SpawnedAgent, AgentStatus, PipelineEvent } from "../types";

interface PipelineStore {
  phase: PhaseId | null;
  status: "idle" | "running" | "done" | "error";
  requirementsDebate: DebateState;
  planDebate: DebateState;
  spawnedAgents: SpawnedAgent[];
  agentStatuses: Record<string, AgentStatus>;
  agentOutputs: Record<string, string>;
  finalOutput: string | null;
  knownIssues: string[];
  error: string | null;

  handleEvent: (event: PipelineEvent) => void;
  reset: () => void;
}

const emptyDebate = (): DebateState => ({ round: 0, messages: [], approved: false });

export const usePipelineStore = create<PipelineStore>((set) => ({
  phase: null,
  status: "idle",
  requirementsDebate: emptyDebate(),
  planDebate: emptyDebate(),
  spawnedAgents: [],
  agentStatuses: {},
  agentOutputs: {},
  finalOutput: null,
  knownIssues: [],
  error: null,

  reset: () =>
    set({
      phase: null,
      status: "running",
      requirementsDebate: emptyDebate(),
      planDebate: emptyDebate(),
      spawnedAgents: [],
      agentStatuses: {},
      agentOutputs: {},
      finalOutput: null,
      knownIssues: [],
      error: null,
    }),

  handleEvent: (event) =>
    set((state) => {
      switch (event.type) {
        case "phase_start":
          return { phase: event.phase };

        case "debate_round": {
          const key = event.phase === "requirements" ? "requirementsDebate" : "planDebate";
          return {
            [key]: { ...state[key], round: event.round },
          };
        }

        case "da_message": {
          const key = event.phase === "requirements" ? "requirementsDebate" : "planDebate";
          return {
            [key]: {
              ...state[key],
              messages: [...state[key].messages, { speaker: "DA", content: event.content }],
            },
          };
        }

        case "evaluator_message": {
          const key = event.phase === "requirements" ? "requirementsDebate" : "planDebate";
          return {
            [key]: {
              ...state[key],
              messages: [
                ...state[key].messages,
                { speaker: "Evaluator", content: event.content, approved: event.approved, critique: event.critique },
              ],
            },
          };
        }

        case "debate_approved": {
          const key = event.phase === "requirements" ? "requirementsDebate" : "planDebate";
          return { [key]: { ...state[key], approved: true } };
        }

        case "agents_spawned":
          return { spawnedAgents: event.agents };

        case "agent_started":
          return {
            agentStatuses: { ...state.agentStatuses, [event.agent_id]: "running" },
          };

        case "agent_done":
          return {
            agentStatuses: { ...state.agentStatuses, [event.agent_id]: "done" },
            agentOutputs: { ...state.agentOutputs, [event.agent_id]: event.output },
          };

        case "final_output":
          return { finalOutput: event.content, knownIssues: event.known_issues || [] };

        case "done":
          return { status: "done" };

        case "error":
          return { status: "error", error: event.message };

        default:
          return {};
      }
    }),
}));
