"use client";

import { useCallback, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  MarkerType,
  NodeMouseHandler,
} from "reactflow";
import "reactflow/dist/style.css";
import { api, EntityOut } from "@/lib/api";
import TopBar from "@/components/TopBar";
import { Search } from "lucide-react";

// ── Vivid, distinct hue per entity type ───────────────────────────────────────
const TYPE_COLOR: Record<string, string> = {
  Equipment:   "#38bdf8", // sky blue
  Part:        "#fb923c", // orange
  Plant:       "#34d399", // emerald
  Department:  "#a78bfa", // violet
  Engineer:    "#f472b6", // pink
  Incident:    "#f87171", // red
  FailureCode: "#fbbf24", // amber
  Standard:    "#94a3b8", // slate
};

function colorFor(type: string) {
  return TYPE_COLOR[type] ?? "#60a5fa";
}

// Minimum arc length (px) between neighbour centres so they never crowd
const MIN_ARC_PX = 120;

function buildGraph(
  center: EntityOut,
  relationships: {
    source_entity_id: string;
    target_entity_id: string;
    relation_type: string;
  }[],
  neighbors: EntityOut[]
) {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const n = Math.max(neighbors.length, 1);
  // Radius grows with count so spacing stays constant
  const radius = Math.max(280, (MIN_ARC_PX * n) / (2 * Math.PI));

  // ── Center node — large glowing pill ──────────────────────────────────────
  const cc = colorFor(center.entity_type);
  nodes.push({
    id: center.id,
    data: { label: center.name },
    position: { x: 0, y: 0 },
    style: {
      background: cc,
      color: "#050a0d",
      border: `3px solid ${cc}`,
      boxShadow: `0 0 22px 6px ${cc}55, 0 0 8px 2px ${cc}`,
      borderRadius: 999,
      padding: "10px 20px",
      fontSize: 13,
      fontWeight: 700,
      whiteSpace: "nowrap",
      textAlign: "center",
      minWidth: 80,
    },
  });

  // ── Neighbour nodes — tinted pills, vivid border ───────────────────────────
  neighbors.forEach((nb, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2; // start at top
    const nc = colorFor(nb.entity_type);
    nodes.push({
      id: nb.id,
      data: { label: nb.name },
      position: {
        x: radius * Math.cos(angle),
        y: radius * Math.sin(angle),
      },
      style: {
        background: `${nc}1a`,          // ~10 % tint
        color: nc,
        border: `2px solid ${nc}`,
        boxShadow: `0 0 10px 2px ${nc}40`,
        borderRadius: 999,
        padding: "7px 14px",
        fontSize: 12,
        fontWeight: 600,
        whiteSpace: "nowrap",
        textAlign: "center",
        minWidth: 60,
        cursor: "pointer",
      },
    });
  });

  // ── Edges — brighter stroke, label on a dark chip ─────────────────────────
  relationships.forEach((r) => {
    const peer =
      neighbors.find(
        (nb) =>
          nb.id === r.target_entity_id || nb.id === r.source_entity_id
      )?.entity_type ?? "";
    const ec = colorFor(peer);
    edges.push({
      id: `${r.source_entity_id}-${r.target_entity_id}-${r.relation_type}`,
      source: r.source_entity_id,
      target: r.target_entity_id,
      label: r.relation_type,
      labelStyle: { fill: "#e2e8f0", fontSize: 9, fontWeight: 600 },
      labelBgStyle: { fill: "#0f1e28", fillOpacity: 0.92, rx: 4, ry: 4 },
      labelBgPadding: [4, 6] as [number, number],
      style: { stroke: `${ec}bb`, strokeWidth: 1.5 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: `${ec}bb`,
        width: 14,
        height: 14,
      },
    });
  });

  return { nodes, edges };
}

export default function GraphPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<EntityOut[]>([]);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [centerName, setCenterName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function doSearch() {
    if (!query.trim()) return;
    setError(null);
    try {
      const r = await api.graphSearch(query);
      setResults(r);
      if (r.length === 1) loadEntity(r[0].id);
    } catch (e) {
      setError(String(e));
    }
  }

  const loadEntity = useCallback(async (id: string) => {
    try {
      const g = await api.graphEntity(id);
      const { nodes, edges } = buildGraph(g.entity, g.relationships, g.neighbors);
      setNodes(nodes);
      setEdges(edges);
      setCenterName(g.entity.name);
      setResults([]);
    } catch (e) {
      setError(String(e));
    }
  }, []);

  // Click any neighbour node in the canvas to re-centre the graph on it
  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      if (node.id) loadEntity(node.id);
    },
    [loadEntity]
  );

  return (
    <div className="flex flex-col h-screen">
      <TopBar title="Knowledge Graph" />
      <div className="p-6 pb-0">
        <div className="flex gap-2 max-w-lg">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && doSearch()}
            placeholder="Search equipment, part, engineer, plant…"
            className="flex-1 px-3 py-2 rounded-sm text-sm outline-none"
            style={{
              background: "var(--panel)",
              border: "1px solid var(--line)",
              color: "var(--text)",
            }}
          />
          <button
            onClick={doSearch}
            className="px-3 py-2 rounded-sm text-sm flex items-center gap-2"
            style={{ background: "var(--panel-raised)", color: "var(--blue)" }}
          >
            <Search size={14} />
            Search
          </button>
        </div>

        {error && (
          <div className="text-xs mt-2" style={{ color: "var(--red)" }}>
            {error}
          </div>
        )}

        {results.length > 1 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {results.map((r) => (
              <button
                key={r.id}
                onClick={() => loadEntity(r.id)}
                className="text-xs mono px-2 py-1 rounded-sm"
                style={{
                  background: "var(--panel-raised)",
                  color: colorFor(r.entity_type),
                }}
              >
                {r.name} · {r.entity_type}
              </button>
            ))}
          </div>
        )}

        {centerName && (
          <div className="text-xs mt-3 mono" style={{ color: "var(--text-faint)" }}>
            Centred on{" "}
            <span style={{ color: "var(--amber)" }}>{centerName}</span> — click
            any neighbour node to re-centre.
          </div>
        )}
      </div>

      <div className="flex-1 mt-4">
        {nodes.length === 0 ? (
          <div className="p-6 text-sm" style={{ color: "var(--text-faint)" }}>
            Search for an entity (try &quot;Pump P204&quot;) to visualise its
            place in the knowledge graph — what it uses, where it&apos;s
            located, who maintains it, and what it has failed because of.
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodeClick={onNodeClick}
            fitView
            fitViewOptions={{ padding: 0.25 }}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#1e293b" gap={24} size={1} />
            <Controls />
          </ReactFlow>
        )}
      </div>
    </div>
  );
}
