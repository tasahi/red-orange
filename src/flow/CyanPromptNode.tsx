import React, { useState, useMemo } from "react";
import { Handle, Position } from "@xyflow/react";
import type { NodeProps } from "@xyflow/react";
import type { ReactFlowNodeData } from "./types.ts";
import { inferTemplatePorts, computeDynamicPortLayouts } from "./cyanViewModel.ts";

export interface CyanPromptNodeProps extends NodeProps {
  data: ReactFlowNodeData;
  onExecute?: (nodeId: string) => void;
}

/**
 * CyanPromptNode: Interactive React Flow Custom Node
 * 
 * Features:
 * - Dynamic Port Inferrer: Auto-mounts input handles corresponding to {{ inputs.<var> }}
 * - Live Prompt Template Editor with token counter
 * - Real-time streaming response preview
 * - Static and dynamic attribute chips
 */
export const CyanPromptNode: React.FC<CyanPromptNodeProps> = ({ id, data, selected, onExecute }) => {
  const config = data.config || {};
  const [template, setTemplate] = useState<string>(
    typeof config.template === "string"
      ? config.template
      : "Analyze: {{ inputs.data.text_content }}"
  );
  const [streamingText, setStreamingText] = useState<string>(
    typeof config.lastOutput === "string" ? config.lastOutput : ""
  );
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);

  // Inferred dynamic ports based on template text
  const portNames = useMemo(() => inferTemplatePorts(template), [template]);
  const inputPorts = useMemo(() => computeDynamicPortLayouts(portNames), [portNames]);

  // Static tags and dynamic attributes
  const staticDomain = (config.staticAttributes as Record<string, unknown>)?.domain as string || "general";
  const dynamicSentiment = (config.dynamicAttributes as Record<string, unknown>)?.sentiment as string;

  const handleTemplateChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const nextVal = e.target.value;
    setTemplate(nextVal);
    config.template = nextVal;
  };

  const handleRun = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExecuting(true);
    if (onExecute) {
      onExecute(id);
    } else {
      // Local preview simulation if no global executor is wired
      setTimeout(() => {
        setStreamingText(`[Synthesized Analysis from ${portNames.length} inputs]: Output generated successfully.`);
        setIsExecuting(false);
      }, 500);
    }
  };

  return (
    <div
      className={`relative flex flex-col min-w-[240px] max-w-[320px] bg-white dark:bg-[#1e293b] rounded-lg shadow-md border text-xs select-none transition-all ${
        selected ? "border-[#06b6d4] ring-2 ring-[#06b6d4]/40" : "border-gray-300 dark:border-slate-700"
      }`}
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      {/* Dynamic Target (Input) Handles */}
      {inputPorts.map((port) => (
        <div key={port.id} className="relative">
          <Handle
            id={port.id}
            type="target"
            position={Position.Left}
            style={{
              top: `${port.topPercent}%`,
              width: 10,
              height: 10,
              background: "#06b6d4",
              border: "2px solid #fff",
              borderRadius: "50%",
              left: -5,
            }}
          />
          {port.name !== "in" && (
            <span
              className="absolute left-2.5 text-[9px] text-[#0891b2] dark:text-[#38bdf8] font-mono pointer-events-none"
              style={{ top: `${port.topPercent - 4}%` }}
            >
              {port.name}
            </span>
          )}
        </div>
      ))}

      {/* Header Bar */}
      <div className="flex items-center justify-between px-3 py-2 bg-slate-50 dark:bg-slate-800/80 border-b border-gray-200 dark:border-slate-700 rounded-t-lg">
        <div className="flex items-center gap-1.5 font-semibold text-slate-800 dark:text-slate-100">
          <span className="w-2.5 h-2.5 rounded-full bg-[#06b6d4]" />
          <span>{data.label || "Prompt Transform"}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-[10px] bg-cyan-100 dark:bg-cyan-900/60 text-cyan-800 dark:text-cyan-200 px-1.5 py-0.5 rounded font-mono">
            {config.model as string || "gpt-4o"}
          </span>
          <button
            type="button"
            onClick={handleRun}
            disabled={isExecuting}
            className="p-1 rounded bg-[#06b6d4] hover:bg-[#0891b2] text-white font-bold text-[10px] leading-none transition-colors"
            title="Execute Prompt"
          >
            {isExecuting ? "..." : "▶"}
          </button>
        </div>
      </div>

      {/* Attribute Chips */}
      <div className="flex flex-wrap items-center gap-1 px-3 py-1.5 bg-slate-100/60 dark:bg-slate-900/40 text-[10px]">
        <span className="bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 px-1.5 py-0.5 rounded">
          #{staticDomain}
        </span>
        {dynamicSentiment && (
          <span className="bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 px-1.5 py-0.5 rounded">
            sentiment: {dynamicSentiment}
          </span>
        )}
        <span className="text-gray-400 dark:text-slate-500 ml-auto font-mono">
          {portNames.length} {portNames.length === 1 ? "input" : "inputs"}
        </span>
      </div>

      {/* Template Editor Area */}
      <div className="p-2.5">
        <div className="flex items-center justify-between pb-1 text-[10px] text-gray-500 dark:text-gray-400">
          <span>Prompt Template</span>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-cyan-600 dark:text-cyan-400 hover:underline"
          >
            {isExpanded ? "Collapse" : "Expand"}
          </button>
        </div>
        <textarea
          value={template}
          onChange={handleTemplateChange}
          rows={isExpanded ? 6 : 3}
          className="w-full text-[11px] font-mono p-1.5 bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded focus:ring-1 focus:ring-cyan-500 focus:outline-none resize-none"
          placeholder="Use {{ inputs.<name> }} for dynamic variables..."
        />
      </div>

      {/* Streaming / Output Preview */}
      {streamingText && (
        <div className="mx-2.5 mb-2.5 p-2 bg-cyan-50/50 dark:bg-slate-800/60 border border-cyan-100 dark:border-cyan-900/40 rounded text-[11px] text-slate-800 dark:text-slate-200">
          <div className="text-[9px] uppercase tracking-wider font-bold text-cyan-700 dark:text-cyan-400 pb-1">
            Output Preview
          </div>
          <div className="max-h-24 overflow-y-auto whitespace-pre-wrap font-sans">
            {streamingText}
          </div>
        </div>
      )}

      {/* Output Port Handle */}
      <Handle
        id="out-0"
        type="source"
        position={Position.Right}
        style={{
          top: "50%",
          width: 10,
          height: 10,
          background: "#0891b2",
          border: "2px solid #fff",
          borderRadius: "50%",
          right: -5,
        }}
      />
    </div>
  );
};

