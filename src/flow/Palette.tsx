import React, { useState } from "react";
import { getCatalogGroupedByCategory, NodeCatalogItem } from "./catalog.ts";
import { createDragPayload, RED_ORANGE_DND_MIME } from "./paletteDnd.ts";

export interface PaletteProps {
  onNodeSelect?: (item: NodeCatalogItem) => void;
}

/**
 * Palette Component
 * Replicates Node-RED's left sidebar accordion palette:
 * - Search / filter box
 * - Category accordions (OR Data, OR Transform, OR Model, etc.)
 * - Node pills with custom category badge colors
 * - HTML5 drag-and-drop to canvas
 */
export const Palette: React.FC<PaletteProps> = ({ onNodeSelect }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const grouped = getCatalogGroupedByCategory();
  const [openCategories, setOpenCategories] = useState<Record<string, boolean>>({
    "OR Data": true,
    "OR Model": true,
  });

  const toggleCategory = (cat: string) => {
    setOpenCategories((prev) => ({
      ...prev,
      [cat]: !prev[cat],
    }));
  };

  const handleDragStart = (e: React.DragEvent<HTMLDivElement>, item: NodeCatalogItem) => {
    const payload = createDragPayload(item.type);
    e.dataTransfer.setData(RED_ORANGE_DND_MIME, JSON.stringify(payload));
    e.dataTransfer.effectAllowed = "move";
  };

  return (
    <aside className="w-56 h-full flex flex-col bg-[#f0f0f0] dark:bg-[#1f1f1f] border-r border-gray-300 dark:border-gray-700 select-none">
      {/* Search Header */}
      <div className="p-2 border-b border-gray-300 dark:border-gray-700">
        <input
          type="text"
          placeholder="Filter nodes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-2 py-1 text-xs rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-[#2b2b2b] text-gray-800 dark:text-gray-100 focus:outline-none focus:border-[#ff6600]"
        />
      </div>

      {/* Accordion Categories */}
      <div className="flex-1 overflow-y-auto p-1 space-y-1">
        {Object.entries(grouped).map(([category, items]) => {
          const filteredItems = items.filter(
            (i) =>
              i.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
              i.type.toLowerCase().includes(searchTerm.toLowerCase())
          );

          if (filteredItems.length === 0) return null;

          const isOpen = searchTerm ? true : openCategories[category] ?? false;

          return (
            <div key={category} className="rounded overflow-hidden">
              <button
                type="button"
                onClick={() => toggleCategory(category)}
                className="w-full flex items-center justify-between px-2 py-1 text-xs font-semibold text-gray-600 dark:text-gray-300 bg-gray-200 dark:bg-[#2a2a2a] hover:bg-gray-300 dark:hover:bg-[#333] cursor-pointer"
              >
                <span>{category}</span>
                <span className="text-[10px] text-gray-500">{isOpen ? "▲" : "▼"}</span>
              </button>

              {isOpen && (
                <div className="p-1 space-y-1 bg-white/50 dark:bg-black/20">
                  {filteredItems.map((item) => (
                    <div
                      key={item.type}
                      draggable
                      onDragStart={(e) => handleDragStart(e, item)}
                      onClick={() => onNodeSelect?.(item)}
                      className="flex items-center h-7 px-1.5 rounded bg-white dark:bg-[#2b2b2b] hover:border-[#ff6600] border border-gray-300 dark:border-gray-600 shadow-xs cursor-grab active:cursor-grabbing transition-all text-xs"
                      title={item.description}
                    >
                      <div
                        className="w-3.5 h-3.5 rounded-sm mr-2 flex-shrink-0"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="truncate text-gray-700 dark:text-gray-200">{item.label}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
};

