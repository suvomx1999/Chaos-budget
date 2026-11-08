/**
 * AlternatePathsViz — branching timeline with expandable alternate paths.
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GitBranch, ChevronDown, ChevronUp } from "lucide-react";
import type { AlternatePath } from "../../types";

interface AlternatePathsVizProps {
  paths: AlternatePath[];
  pivotEvents: string[];
}

function outcomeColor(level: string): string {
  switch (level.toLowerCase()) {
    case "executive":
    case "lead":
      return "#10b981";
    case "senior":
      return "#06b6d4";
    case "mid":
      return "#3b82f6";
    case "junior":
      return "#f59e0b";
    case "student":
      return "#ef4444";
    default:
      return "#64748b";
  }
}

export default function AlternatePathsViz({ paths, pivotEvents }: AlternatePathsVizProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const displayPaths = paths.slice(0, 5);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
    >
      {/* Pivot events */}
      {pivotEvents.length > 0 && (
        <div className="mb-5">
          <h4 className="text-[10px] text-text-dim uppercase tracking-wider mb-2">
            Key Pivot Points
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {pivotEvents.map((event, i) => (
              <span
                key={i}
                className="px-2.5 py-1 rounded-full bg-primary/[0.06] border border-primary/[0.12] text-[10px] text-primary font-medium"
              >
                {event}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Paths */}
      <div className="space-y-2">
        {displayPaths.map((path, i) => {
          const isExpanded = expandedId === path.path_id;
          const color = outcomeColor(path.outcome_level);

          return (
            <motion.div
              key={path.path_id}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.08 * i }}
              className="border border-white/[0.05] rounded-xl overflow-hidden bg-white/[0.015] hover:border-white/[0.08] transition-colors"
            >
              <button
                onClick={() => setExpandedId(isExpanded ? null : path.path_id)}
                className="w-full flex items-center gap-3 p-3.5 text-left"
              >
                <div className="flex-shrink-0">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${color}10` }}
                  >
                    <GitBranch className="h-4 w-4" style={{ color }} />
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <span className="font-medium text-xs text-text truncate block">
                    {path.final_outcome}
                  </span>
                  <p className="text-[10px] text-text-dim mt-0.5 truncate">
                    Diverged at: {path.divergence_point}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className="px-2 py-0.5 rounded text-[10px] font-mono font-medium"
                    style={{ color, backgroundColor: `${color}10` }}
                  >
                    {path.outcome_level}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="h-3.5 w-3.5 text-text-dim" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5 text-text-dim" />
                  )}
                </div>
              </button>

              <AnimatePresence>
                {isExpanded && path.events.length > 0 && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="overflow-hidden"
                  >
                    <div className="px-3.5 pb-3.5 pt-1 border-t border-white/[0.04]">
                      <p className="text-[10px] text-text-dim mb-2">Simulated events:</p>
                      <div className="space-y-1.5">
                        {path.events.slice(0, 6).map((evt, j) => (
                          <div key={j} className="flex items-start gap-2 text-xs">
                            <div
                              className="w-1 h-1 rounded-full mt-1.5 flex-shrink-0"
                              style={{ backgroundColor: color }}
                            />
                            <span className="text-text-muted">
                              {typeof evt === "object"
                                ? String(
                                    (evt as Record<string, unknown>).description ||
                                    (evt as Record<string, unknown>).title ||
                                    JSON.stringify(evt)
                                  )
                                : String(evt)}
                            </span>
                          </div>
                        ))}
                        {path.events.length > 6 && (
                          <p className="text-[10px] text-text-dim/50 pl-3">
                            +{path.events.length - 6} more…
                          </p>
                        )}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </div>

      {paths.length > 5 && (
        <p className="text-center text-[10px] text-text-dim mt-3">
          Showing 5 of {paths.length} alternate paths
        </p>
      )}
    </motion.div>
  );
}
