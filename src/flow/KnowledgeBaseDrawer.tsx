import React, { useState } from "react";
import { JsonRpcClient } from "./rpcClient.ts";

export interface KnowledgeBaseQueryResult {
  node_id: string;
  run_id: string;
  text_content: string;
  structured_data: Record<string, unknown>;
  static_attributes: Record<string, unknown>;
  dynamic_attributes: Record<string, unknown>;
  lineage: string[];
  score: number;
}

export interface KnowledgeBaseDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  selectedNodeIds: string[];
  rpcClient?: JsonRpcClient;
}

/**
 * KnowledgeBaseDrawer: Subgraph-Scoped Conversational Insight Studio
 * Allows analysts to query the living Knowledge Base grounded strictly on selected nodes or the entire canvas.
 */
export const KnowledgeBaseDrawer: React.FC<KnowledgeBaseDrawerProps> = ({
  isOpen,
  onClose,
  selectedNodeIds,
  rpcClient,
}) => {
  const [queryText, setQueryText] = useState("");
  const [results, setResults] = useState<KnowledgeBaseQueryResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const client = rpcClient || new JsonRpcClient();

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!queryText.trim() && selectedNodeIds.length === 0) return;

    setIsLoading(true);
    setErrorMsg(null);
    try {
      const res = await client.call<{ results: KnowledgeBaseQueryResult[]; count: number }>(
        "cyan.queryKB",
        {
          query_text: queryText.trim() || undefined,
          scope_node_ids: selectedNodeIds.length > 0 ? selectedNodeIds : undefined,
          top_k: 5,
        }
      );
      setResults(res.results || []);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-y-0 right-0 w-[420px] bg-white dark:bg-slate-900 border-l border-gray-200 dark:border-slate-800 shadow-2xl z-50 flex flex-col text-xs"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3.5 border-b border-gray-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80">
        <div>
          <div className="font-bold text-sm text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#06b6d4]" />
            <span>Knowledge Base Query Studio</span>
          </div>
          <div className="text-[11px] text-gray-500 dark:text-slate-400 mt-0.5">
            {selectedNodeIds.length > 0 ? (
              <span className="text-cyan-600 dark:text-cyan-400 font-medium">
                Scoped to {selectedNodeIds.length} selected node(s)
              </span>
            ) : (
              <span>Global canvas scope</span>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 p-1 font-bold text-base leading-none"
        >
          ✕
        </button>
      </div>

      {/* Query Bar */}
      <form onSubmit={handleSearch} className="p-3 border-b border-gray-200 dark:border-slate-800 flex gap-2">
        <input
          type="text"
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          placeholder="Ask a question or enter keywords..."
          className="flex-1 px-2.5 py-1.5 bg-gray-50 dark:bg-slate-800 border border-gray-300 dark:border-slate-700 rounded focus:ring-1 focus:ring-cyan-500 focus:outline-none text-slate-900 dark:text-slate-100"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="px-3 py-1.5 bg-[#06b6d4] hover:bg-[#0891b2] text-white font-medium rounded transition-colors"
        >
          {isLoading ? "..." : "Search"}
        </button>
      </form>

      {/* Results View */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {errorMsg && (
          <div className="p-2.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-red-600 dark:text-red-400 rounded">
            {errorMsg}
          </div>
        )}

        {results.length === 0 && !isLoading && !errorMsg && (
          <div className="text-center py-8 text-gray-400 dark:text-slate-500">
            {selectedNodeIds.length > 0
              ? "Search within selected node outputs or hit search to list scoped records."
              : "Ask questions regarding data mining findings or prompt syntheses."}
          </div>
        )}

        {results.map((res) => (
          <div
            key={res.run_id}
            className="p-3 bg-gray-50 dark:bg-slate-800/60 border border-gray-200 dark:border-slate-700/80 rounded-lg space-y-1.5"
          >
            <div className="flex items-center justify-between text-[10px]">
              <span className="font-mono text-cyan-600 dark:text-cyan-400 font-semibold">{res.node_id}</span>
              <span className="text-gray-400">Score: {res.score.toFixed(2)}</span>
            </div>

            <div className="text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
              {res.text_content}
            </div>

            {/* Lineage & Provenance Badge */}
            {res.lineage && res.lineage.length > 0 && (
              <div className="text-[10px] text-gray-500 dark:text-slate-400 flex flex-wrap items-center gap-1 pt-1 border-t border-gray-200/50 dark:border-slate-700/50">
                <span>Lineage:</span>
                {res.lineage.map((anc) => (
                  <span key={anc} className="bg-slate-200 dark:bg-slate-700 px-1 py-0.2 rounded font-mono text-[9px]">
                    ← {anc}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

