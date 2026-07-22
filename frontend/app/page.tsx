"use client";

import { useEffect, useState } from "react";
import { api, DashboardStats } from "@/lib/api";
import { StatCard } from "@/components/ui";
import TopBar from "@/components/TopBar";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { useRole } from "@/components/RoleContext";

const CATEGORY_COLORS: Record<string, string> = {
  maintenance_log: "var(--blue)",
  inspection: "var(--amber)",
  safety: "var(--red)",
  manual: "var(--green)",
  uncategorized: "var(--text-faint)",
  general: "var(--text-faint)",
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { role } = useRole();

  useEffect(() => {
    api
      .dashboardStats()
      .then(setStats)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const safetyFirst = role === "Safety Officer";

  return (
    <div>
      <TopBar title="Operations Dashboard" />
      <div className="p-6 space-y-6">
        {error && (
          <div className="panel p-4 text-sm" style={{ color: "var(--red)" }}>
            Could not reach the backend API at the configured NEXT_PUBLIC_API_URL — is it running? ({error})
          </div>
        )}

        {loading && !error && (
          <div className="text-sm" style={{ color: "var(--text-dim)" }}>
            Loading fleet statistics…
          </div>
        )}

        {stats && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <StatCard label="Documents ingested" value={stats.total_documents} />
              <StatCard label="Equipment tracked" value={stats.total_equipment} />
              <StatCard label="Recorded incidents" value={stats.total_incidents} sub="failure events, trailing log" />
              <StatCard
                label="High-risk equipment"
                value={stats.open_high_risk_equipment}
                sub={safetyFirst ? "prioritized for your role" : undefined}
              />
              <StatCard label="Avg. compliance score" value={stats.compliance_score_avg ? `${stats.compliance_score_avg}%` : "—"} sub="run checks under Agents" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="panel p-5 lg:col-span-2">
                <div className="text-sm font-medium mb-4" style={{ color: "var(--text)" }}>
                  Failure trend (last 12 months)
                </div>
                {stats.failure_trend.length === 0 ? (
                  <div className="text-sm" style={{ color: "var(--text-faint)" }}>
                    No failure events recorded in this window.
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={stats.failure_trend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" />
                      <XAxis dataKey="month" tick={{ fill: "var(--text-faint)", fontSize: 11 }} />
                      <YAxis tick={{ fill: "var(--text-faint)", fontSize: 11 }} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{ background: "var(--panel-raised)", border: "1px solid var(--line)", fontSize: 12 }}
                      />
                      <Bar dataKey="failures" fill="var(--amber)" radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>

              <div className="panel p-5">
                <div className="text-sm font-medium mb-4" style={{ color: "var(--text)" }}>
                  Documents by category
                </div>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={Object.entries(stats.docs_by_category).map(([name, value]) => ({ name, value }))}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={45}
                      outerRadius={75}
                    >
                      {Object.keys(stats.docs_by_category).map((k) => (
                        <Cell key={k} fill={CATEGORY_COLORS[k] || "var(--text-faint)"} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: "var(--panel-raised)", border: "1px solid var(--line)", fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-wrap gap-3 mt-2">
                  {Object.entries(stats.docs_by_category).map(([k, v]) => (
                    <div key={k} className="flex items-center gap-1.5 text-[11px]" style={{ color: "var(--text-dim)" }}>
                      <span className="w-2 h-2 rounded-full" style={{ background: CATEGORY_COLORS[k] || "var(--text-faint)" }} />
                      {k} ({v})
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="panel p-5">
              <div className="text-sm font-medium mb-2" style={{ color: "var(--text)" }}>
                Quick actions
              </div>
              <div className="flex gap-3 flex-wrap text-sm">
                <a href="/copilot" className="px-3 py-1.5 rounded-sm" style={{ background: "var(--panel-raised)", color: "var(--blue)" }}>
                  Ask the copilot →
                </a>
                <a href="/agents" className="px-3 py-1.5 rounded-sm" style={{ background: "var(--panel-raised)", color: "var(--amber)" }}>
                  Run root cause analysis →
                </a>
                <a href="/documents" className="px-3 py-1.5 rounded-sm" style={{ background: "var(--panel-raised)", color: "var(--green)" }}>
                  Upload a document →
                </a>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
