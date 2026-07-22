export function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="panel p-5">
      <div className="text-[11px] uppercase tracking-wider" style={{ color: "var(--text-faint)" }}>
        {label}
      </div>
      <div className="mono text-3xl font-semibold mt-2" style={{ color: "var(--text)" }}>
        {value}
      </div>
      {sub && (
        <div className="text-xs mt-1" style={{ color: "var(--text-dim)" }}>
          {sub}
        </div>
      )}
    </div>
  );
}

export function RiskBadge({ level }: { level: string }) {
  const colors: Record<string, { bg: string; fg: string }> = {
    High: { bg: "var(--red-dim)", fg: "var(--red)" },
    Medium: { bg: "var(--amber-dim)", fg: "var(--amber)" },
    Low: { bg: "var(--green-dim)", fg: "var(--green)" },
    Unknown: { bg: "var(--panel-raised)", fg: "var(--text-faint)" },
  };
  const c = colors[level] || colors.Unknown;
  return (
    <span
      className="mono text-[11px] px-2 py-0.5 rounded-sm uppercase tracking-wide"
      style={{ background: c.bg, color: c.fg }}
    >
      {level}
    </span>
  );
}

export function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 60 ? "var(--green)" : pct >= 30 ? "var(--amber)" : "var(--red)";
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-1.5 rounded-full overflow-hidden" style={{ background: "var(--panel-raised)" }}>
        <div className="h-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="mono text-[11px]" style={{ color: "var(--text-faint)" }}>
        {pct}%
      </span>
    </div>
  );
}
