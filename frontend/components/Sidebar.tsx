"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MessageSquare, FileStack, GitBranch, Cpu, Activity } from "lucide-react";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/copilot", label: "Copilot", icon: MessageSquare },
  { href: "/documents", label: "Documents", icon: FileStack },
  { href: "/graph", label: "Knowledge Graph", icon: GitBranch },
  { href: "/agents", label: "Agents", icon: Cpu },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="w-60 shrink-0 border-r flex flex-col h-screen sticky top-0"
      style={{ borderColor: "var(--line)", background: "var(--panel)" }}
    >
      <div className="px-5 py-5 border-b" style={{ borderColor: "var(--line)" }}>
        <div className="flex items-center gap-2">
          <Activity size={20} color="var(--amber)" />
          <span className="font-semibold tracking-tight text-sm" style={{ color: "var(--text)" }}>
            ASSET &amp; OPS BRAIN
          </span>
        </div>
        <div className="mono text-[10px] mt-1" style={{ color: "var(--text-faint)" }}>
          v0.1 — industrial knowledge platform
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 px-3 py-2 rounded-sm text-sm transition-colors"
              style={{
                background: active ? "var(--panel-raised)" : "transparent",
                color: active ? "var(--amber)" : "var(--text-dim)",
                borderLeft: active ? "2px solid var(--amber)" : "2px solid transparent",
              }}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-5 py-4 border-t text-[11px] mono" style={{ borderColor: "var(--line)", color: "var(--text-faint)" }}>
        Tier 1+2 demo scope
        <br />
        Neo4j / RBAC / voice: roadmap
      </div>
    </aside>
  );
}
