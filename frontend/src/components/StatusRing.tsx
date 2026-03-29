import type { AgentStatus } from "../types";

interface Props {
  status: AgentStatus;
  size?: number;
}

export function StatusRing({ status, size = 56 }: Props) {
  const r = (size - 4) / 2;
  const circumference = 2 * Math.PI * r;

  const colorMap: Record<AgentStatus, string> = {
    idle: "#27272A",
    running: "#F97316",
    done: "#F97316",
  };

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        className={status === "running" ? "animate-spin-slow" : ""}
        style={{ position: "absolute", top: 0, left: 0 }}
      >
        {/* Track */}
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#27272A" strokeWidth={2} />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={colorMap[status]}
          strokeWidth={2}
          strokeDasharray={`${status === "running" ? circumference * 0.25 : circumference} ${circumference}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dasharray 0.4s ease, stroke 0.3s ease" }}
        />
      </svg>

      {/* Icon inside ring */}
      <div className="text-lg">
        {status === "idle" && <span className="text-faint">◦</span>}
        {status === "running" && <span className="text-accent animate-pulse">⬡</span>}
        {status === "done" && <span className="text-accent">✓</span>}
      </div>
    </div>
  );
}
