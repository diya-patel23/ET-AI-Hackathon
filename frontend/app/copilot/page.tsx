"use client";

import { useState, useRef, useEffect } from "react";
import { api, Citation } from "@/lib/api";
import TopBar from "@/components/TopBar";
import { ConfidenceBar } from "@/components/ui";
import { Send, FileText } from "lucide-react";

type Message = {
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
  confidence?: number;
  relatedEntities?: string[];
};

const SUGGESTIONS = [
  "Why did Pump P204 fail?",
  "Show maintenance history for Compressor C305",
  "What PPE is required near rotating equipment?",
  "Which equipment has overdue certifications?",
];

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(query: string) {
    if (!query.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text: query }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.chat(query);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: res.answer, citations: res.citations, confidence: res.confidence, relatedEntities: res.related_entities },
      ]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: `Request failed: ${e}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <TopBar title="Industrial Copilot" />

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="panel p-5">
            <div className="text-sm mb-3" style={{ color: "var(--text-dim)" }}>
              Ask about equipment history, failures, inspections, or safety requirements. Every answer
              cites the specific documents it drew from.
            </div>
            <div className="flex flex-wrap gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-xs px-2.5 py-1.5 rounded-sm"
                  style={{ background: "var(--panel-raised)", color: "var(--blue)" }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className="max-w-2xl rounded-sm px-4 py-3 text-sm"
              style={{
                background: m.role === "user" ? "var(--blue-dim)" : "var(--panel)",
                border: m.role === "assistant" ? "1px solid var(--line)" : "none",
                color: "var(--text)",
              }}
            >
              <div className="whitespace-pre-wrap">{m.text}</div>

              {m.confidence !== undefined && (
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-[11px]" style={{ color: "var(--text-faint)" }}>
                    Confidence
                  </span>
                  <ConfidenceBar value={m.confidence} />
                </div>
              )}

              {m.citations && m.citations.length > 0 && (
                <div className="mt-3 space-y-1.5 border-t pt-2" style={{ borderColor: "var(--line)" }}>
                  <div className="text-[11px] uppercase tracking-wide" style={{ color: "var(--text-faint)" }}>
                    Sources
                  </div>
                  {m.citations.map((c, ci) => (
                    <div key={ci} className="flex items-start gap-1.5 text-[11px]" style={{ color: "var(--text-dim)" }}>
                      <FileText size={12} className="mt-0.5 shrink-0" />
                      <span className="mono">{c.filename}</span>
                    </div>
                  ))}
                </div>
              )}

              {m.relatedEntities && m.relatedEntities.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {m.relatedEntities.map((e) => (
                    <span
                      key={e}
                      className="mono text-[10px] px-1.5 py-0.5 rounded-sm"
                      style={{ background: "var(--panel-raised)", color: "var(--amber)" }}
                    >
                      {e}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="text-xs mono" style={{ color: "var(--text-faint)" }}>
            retrieving + synthesizing…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t p-4" style={{ borderColor: "var(--line)" }}>
        <div className="flex gap-2 max-w-3xl">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send(input)}
            placeholder="Ask about equipment, failures, inspections…"
            className="flex-1 px-3 py-2.5 rounded-sm text-sm outline-none"
            style={{ background: "var(--panel)", border: "1px solid var(--line)", color: "var(--text)" }}
          />
          <button
            onClick={() => send(input)}
            disabled={loading}
            className="px-4 py-2.5 rounded-sm flex items-center gap-2 text-sm"
            style={{ background: "var(--amber)", color: "#14100a" }}
          >
            <Send size={14} />
            Ask
          </button>
        </div>
      </div>
    </div>
  );
}
