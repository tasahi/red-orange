import React from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import { computeNodeViewModel } from "./nodeViewModel.ts";
import { ReactFlowNodeData } from "./types.ts";

export interface OrangeNodeProps extends NodeProps {
  data: ReactFlowNodeData;
  onTrigger?: (nodeId: string) => void;
}

/**
 * OrangeNode: Custom React Flow Node Component
 * Replicates the standard Node-RED node look and feel:
 * - Rounded pill shape with dark/light themed border
 * - Colored left badge representing category color
 * - Stacked input (left) and output (right) port handles
 * - Status indicator beneath node
 * - Optional manual trigger button (for inject / manual nodes)
 */
export const OrangeNode: React.FC<OrangeNodeProps> = ({ id, data, selected, onTrigger }) => {
  const vm = computeNodeViewModel(data);

  return (
    <div
      className={`relative flex items-center min-w-[140px] max-w-[220px] h-[36px] bg-white dark:bg-[#2e2e2e] rounded-md shadow-sm border text-xs select-none transition-all ${
        selected ? "border-[#ff6600] ring-2 ring-[#ff6600]/30" : "border-gray-300 dark:border-gray-600"
      }`}
      style={{
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      }}
    >
      {/* Target (Input) Handles */}
      {vm.inputPorts.map((port) => (
        <Handle
          key={port.id}
          id={port.id}
          type="target"
          position={Position.Left}
          style={{
            top: `${port.topPercent}%`,
            width: 10,
            height: 10,
            background: "#888",
            border: "2px solid #fff",
            borderRadius: "50%",
            left: -5,
          }}
        />
      ))}

      {/* Manual Trigger Button (e.g. for Inject or Bridge nodes) */}
      {vm.hasTriggerButton && (
        <button
          type="button"
          title="Trigger Node"
          onClick={(e) => {
            e.stopPropagation();
            onTrigger?.(id);
          }}
          className="flex items-center justify-center w-5 h-full bg-black/10 hover:bg-black/20 dark:bg-white/10 dark:hover:bg-white/20 border-r border-gray-300 dark:border-gray-600 rounded-l cursor-pointer"
        >
          <div className="w-2 h-2 bg-[#d9534f] rounded-full" />
        </button>
      )}

      {/* Category Colored Icon Badge */}
      <div
        className="w-7 h-full flex items-center justify-center font-bold text-white text-[10px] rounded-l-sm flex-shrink-0"
        style={{ backgroundColor: vm.badgeColor }}
      >
        {vm.catalogItem.label.slice(0, 2).toUpperCase()}
      </div>

      {/* Node Label & Subtitle */}
      <div className="flex-1 px-2.5 truncate font-medium text-gray-800 dark:text-gray-100">
        <span className="truncate">{vm.label}</span>
      </div>

      {/* Source (Output) Handles */}
      {vm.outputPorts.map((port) => (
        <Handle
          key={port.id}
          id={port.id}
          type="source"
          position={Position.Right}
          style={{
            top: `${port.topPercent}%`,
            width: 10,
            height: 10,
            background: "#555",
            border: "2px solid #fff",
            borderRadius: "50%",
            right: -5,
          }}
        />
      ))}

      {/* Status Pill (Rendered underneath node when active) */}
      {data.status && (
        <div className="absolute -bottom-5 left-1 flex items-center gap-1 text-[10px] text-gray-500 dark:text-gray-400">
          <span
            className="w-1.5 h-1.5 rounded-full inline-block"
            style={{
              backgroundColor:
                data.status.fill === "green"
                  ? "#52c41a"
                  : data.status.fill === "red"
                  ? "#ff4d4f"
                  : data.status.fill === "yellow"
                  ? "#faad14"
                  : "#1890ff",
            }}
          />
          <span className="truncate max-w-[160px]">{data.status.text}</span>
        </div>
      )}
    </div>
  );
};

