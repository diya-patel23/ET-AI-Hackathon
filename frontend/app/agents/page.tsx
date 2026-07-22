"use client";

import { useEffect, useState } from "react";
import TopBar from "@/components/TopBar";
import { RiskBadge, ConfidenceBar } from "@/components/ui";
import { api, RootCauseResponse, MaintenanceResponse, ComplianceResponse, DocumentOut } from "@/lib/api";
import { Loader2, GitCommit, Gauge, ShieldCheck } from "lucide-react";

type Tab = "root-cause" | "maintenance" | "compliance";

const TABS: { id: Tab; label: string; icon: typeof GitCommit }[] = [
  { id: "root-cause", label: "Root Cause Analysis", icon: GitCommit },
  { id: "maintenance", label: "Maintenance Intelligence", icon: Gauge },
  { id: "compliance", label: "Compliance Check", icon: ShieldCheck },
];

export default function AgentsPage() {
  const [tab, setTab] = useState<Tab>("root-cause");

  return (
    <div>
      <TopBar title="AI Agents" />
      <div className="p-6 space-y-6">
        <div className="flex gap-2">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className="flex items-center gap-2 px-3 py-2 rounded-sm text-sm"
              style={{
                background: tab === id ? "var(--panel-raised)" : "transparent",
                color: tab === id ? "var(--amber)" : "var(--text-dim)",
                border: `1px solid ${tab === id ? "var(--amber)" : "var(--line)"}`,
              }}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>

        {tab === "root-cause" && <RootCauseTab />}
        {tab === "maintenance" && <MaintenanceTab />}
        {tab === "compliance" && <ComplianceTab />}
      </div>
    </div>
  );
}

function RootCauseTab() {
  const [equipment, setEquipment] = useState("Pump P204");
  const [result, setResult] = useState<RootCauseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      setResult(await api.rootCause(equipment));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="panel p-5">
        <div className="text-sm mb-3" style={{ color: "var(--text-dim)" }}>
          Collects maintenance history, related documents, and knowledge-graph context to build an
          explainable causal chain from the earliest contributing factor to the final failure.
        </div>
        <div className="flex gap-2 max-w-lg">
          <input
            value={equipment}
            onChange={(e) => setEquipment(e.target.value)}
            placeholder="Equipment name, e.g. Pump P204"
            className="flex-1 px-3 py-2 rounded-sm text-sm outline-none"
            style={{ background: "var(--panel-raised)", border: "1px solid var(--line)", color: "var(--text)" }}
          />
          <button
            onClick={run}
            disabled={loading}
            className="px-4 py-2 rounded-sm text-sm flex items-center gap-2"
            style={{ background: "var(--amber)", color: "#14100a" }}
          >
            {loading && <Loader2 size={14} className="animate-spin" />}
            Analyze
          </button>
        </div>
        {error && <div className="text-xs mt-2" style={{ color: "var(--red)" }}>{error}</div>}
      </div>

      {result && (
        <div className="panel p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-medium" style={{ color: "var(--text)" }}>
              Causal chain — {result.equipment_name}
            </div>
            <ConfidenceBar value={result.confidence} />
          </div>

          {result.chain.length === 0 ? (
            <div className="text-sm" style={{ color: "var(--text-faint)" }}>
              {result.summary}
            </div>
          ) : (
            <div className="space-y-0">
              {result.chain.map((stage, i) => (
                <div key={i} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="w-2.5 h-2.5 rounded-full mt-1.5" style={{ background: "var(--amber)" }} />
                    {i < result.chain.length - 1 && <div className="w-px flex-1" style={{ background: "var(--line)" }} />}
                  </div>
                  <div className="pb-5 min-w-0">
                    <div className="text-sm font-medium mono uppercase tracking-wide" style={{ color: "var(--amber)" }}>
                      {stage.stage}
                    </div>
                    <div className="text-sm mt-1" style={{ color: "var(--text)" }}>
                      {stage.evidence}
                    </div>
                    {stage.source_filename && (
                      <div className="text-[11px] mono mt-1" style={{ color: "var(--text-faint)" }}>
                        source: {stage.source_filename}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-2 pt-4 border-t text-sm" style={{ borderColor: "var(--line)", color: "var(--text-dim)" }}>
            {result.summary}
          </div>
        </div>
      )}
    </div>
  );
}

function MaintenanceTab() {
  const [equipment, setEquipment] = useState("Pump P204");
  const [result, setResult] = useState<MaintenanceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      setResult(await api.maintenance(equipment));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="panel p-5">
        <div className="text-sm mb-3" style={{ color: "var(--text-dim)" }}>
          Scores risk from maintenance recency, failure frequency, and last-failure severity — a simple,
          explainable heuristic, not a trained ML model (see the roadmap for the planned RUL model).
        </div>
        <div className="flex gap-2 max-w-lg">
          <input
            value={equipment}
            onChange={(e) => setEquipment(e.target.value)}
            placeholder="Equipment name, e.g. Pump P204"
            className="flex-1 px-3 py-2 rounded-sm text-sm outline-none"
            style={{ background: "var(--panel-raised)", border: "1px solid var(--line)", color: "var(--text)" }}
          />
          <button
            onClick={run}
            disabled={loading}
            className="px-4 py-2 rounded-sm text-sm flex items-center gap-2"
            style={{ background: "var(--amber)", color: "#14100a" }}
          >
            {loading && <Loader2 size={14} className="animate-spin" />}
            Assess
          </button>
        </div>
        {error && <div className="text-xs mt-2" style={{ color: "var(--red)" }}>{error}</div>}
      </div>

      {result && (
        <div className="panel p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-medium" style={{ color: "var(--text)" }}>
              {result.equipment_name}
            </div>
            <RiskBadge level={result.risk_level} />
          </div>

          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <div className="text-[11px]" style={{ color: "var(--text-faint)" }}>Risk score</div>
              <div className="mono text-xl" style={{ color: "var(--text)" }}>{result.risk_score}</div>
            </div>
            <div>
              <div className="text-[11px]" style={{ color: "var(--text-faint)" }}>Days since last maintenance</div>
              <div className="mono text-xl" style={{ color: "var(--text)" }}>{result.days_since_last_maintenance ?? "—"}</div>
            </div>
            <div>
              <div className="text-[11px]" style={{ color: "var(--text-faint)" }}>Failures (12mo)</div>
              <div className="mono text-xl" style={{ color: "var(--text)" }}>{result.failure_count_last_year}</div>
            </div>
          </div>

          {result.recommended_next_date && (
            <div className="text-[11px] mono mb-3" style={{ color: "var(--text-faint)" }}>
              Recommended next maintenance: {result.recommended_next_date}
            </div>
          )}

          <div className="pt-3 border-t text-sm" style={{ borderColor: "var(--line)", color: "var(--text-dim)" }}>
            {result.recommendation}
          </div>
        </div>
      )}
    </div>
  );
}

function ComplianceTab() {
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [docId, setDocId] = useState("");
  const [result, setResult] = useState<ComplianceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listDocuments({ doc_category: "inspection" }).then((d) => {
      setDocs(d);
      if (d.length > 0) setDocId(d[0].id);
    });
  }, []);

  async function run() {
    if (!docId) return;
    setLoading(true);
    setError(null);
    try {
      setResult(await api.compliance(docId));
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="panel p-5">
        <div className="text-sm mb-3" style={{ color: "var(--text-dim)" }}>
          Checks an inspection report against a small hardcoded rule set (documentation completeness, PPE
          requirements, certification status, pressure limits) rather than a general regulation engine.
        </div>
        <div className="flex gap-2 max-w-lg">
          <select
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            className="flex-1 px-3 py-2 rounded-sm text-sm outline-none"
            style={{ background: "var(--panel-raised)", border: "1px solid var(--line)", color: "var(--text)" }}
          >
            {docs.length === 0 && <option value="">No inspection reports ingested yet</option>}
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename}
              </option>
            ))}
          </select>
          <button
            onClick={run}
            disabled={loading || !docId}
            className="px-4 py-2 rounded-sm text-sm flex items-center gap-2"
            style={{ background: "var(--amber)", color: "#14100a" }}
          >
            {loading && <Loader2 size={14} className="animate-spin" />}
            Check
          </button>
        </div>
        {error && <div className="text-xs mt-2" style={{ color: "var(--red)" }}>{error}</div>}
      </div>

      {result && (
        <div className="panel p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-medium" style={{ color: "var(--text)" }}>
              {result.filename}
            </div>
            <div className="mono text-lg" style={{ color: result.compliance_score >= 80 ? "var(--green)" : result.compliance_score >= 50 ? "var(--amber)" : "var(--red)" }}>
              {result.compliance_score}%
            </div>
          </div>
          <div className="space-y-2">
            {result.results.map((r, i) => (
              <div key={i} className="flex items-start justify-between gap-3 py-2 border-t" style={{ borderColor: "var(--line)" }}>
                <div>
                  <div className="text-sm" style={{ color: "var(--text)" }}>{r.rule}</div>
                  <div className="text-[11px] mono" style={{ color: "var(--text-faint)" }}>{r.standard}</div>
                  <div className="text-[11px] mt-1" style={{ color: "var(--text-dim)" }}>{r.explanation}</div>
                </div>
                <span
                  className="mono text-[11px] px-2 py-0.5 rounded-sm shrink-0"
                  style={{
                    background: r.passed ? "var(--green-dim)" : "var(--red-dim)",
                    color: r.passed ? "var(--green)" : "var(--red)",
                  }}
                >
                  {r.passed ? "PASS" : "FAIL"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
