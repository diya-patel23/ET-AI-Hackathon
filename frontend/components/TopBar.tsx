"use client";

import { useEffect, useState } from "react";
import { api, HealthStatus } from "@/lib/api";
import { useRole } from "@/components/RoleContext";

const ROLES = ["Engineer", "Maintenance Manager", "Safety Officer", "Plant Manager", "Administrator"];

export default function TopBar({ title }: { title: string }) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState(false);
  const { role, setRole } = useRole();

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch(() => setError(true));
  }, []);

  return (
    <div
      className="flex items-center justify-between px-6 py-4 border-b sticky top-0 z-10"
      style={{ borderColor: "var(--line)", background: "var(--ink)" }}
    >
      <h1 className="text-lg font-semibold" style={{ color: "var(--text)" }}>
        {title}
      </h1>

      <div className="flex items-center gap-4">
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="text-xs mono px-2 py-1.5 rounded-sm border"
          style={{ background: "var(--panel)", borderColor: "var(--line)", color: "var(--text-dim)" }}
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>

        <div className="flex items-center gap-1.5 text-[11px] mono">
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: error ? "var(--red)" : health ? "var(--green)" : "var(--text-faint)" }}
          />
          <span style={{ color: "var(--text-faint)" }}>
            {error ? "API unreachable" : health ? `${health.embedding_backend}` : "connecting..."}
          </span>
          {health && !health.llm_configured && (
            <span className="ml-2 px-1.5 py-0.5 rounded-sm" style={{ background: "var(--amber-dim)", color: "var(--amber)" }}>
              LLM not configured
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
