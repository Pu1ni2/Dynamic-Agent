export type PhaseId =
  | "debate_requirements"
  | "debate_plan"
  | "execution"
  | "assembly";

export interface SpawnedAgent {
  id: string;
  role: string;
  model_tier: string;
}

export type AgentStatus = "idle" | "running" | "done";

export interface DebateMessage {
  speaker: "DA" | "Evaluator";
  content: string;
  approved?: boolean;
  critique?: string;
}

export interface DebateState {
  round: number;
  messages: DebateMessage[];
  approved: boolean;
}

export type PipelineEvent =
  | { type: "connected"; session_id: string }
  | { type: "phase_start"; phase: PhaseId; label: string }
  | { type: "debate_round"; phase: string; round: number }
  | { type: "da_message"; phase: string; content: string }
  | { type: "evaluator_message"; phase: string; content: string; approved: boolean; critique: string }
  | { type: "debate_approved"; phase: string }
  | { type: "agents_spawned"; agents: SpawnedAgent[] }
  | { type: "agent_started"; agent_id: string; role: string }
  | { type: "agent_done"; agent_id: string; role: string; output: string }
  | { type: "final_output"; content: string; coverage_report: object; known_issues: string[] }
  | { type: "done"; result: object }
  | { type: "error"; message: string };
