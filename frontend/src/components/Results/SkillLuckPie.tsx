/**
 * SkillLuckPie — donut chart breakdown with dashboard-quality aesthetics.
 */

import { motion } from "framer-motion";

interface SkillLuckPieProps {
  skill: number;
  luck: number;
  timing: number;
}

const SEGMENTS = [
  { key: "skill", label: "Skill", color: "#10b981" },
  { key: "luck", label: "Luck", color: "#f59e0b" },
  { key: "timing", label: "Timing", color: "#3b82f6" },
] as const;

export default function SkillLuckPie({ skill, luck, timing }: SkillLuckPieProps) {
  const values: Record<string, number> = { skill, luck, timing };

  const size = 180;
  const stroke = 20;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;

  let accumulated = 0;
  const segments = SEGMENTS.map((seg) => {
    const pct = values[seg.key];
    const length = (pct / 100) * circumference;
    const gap = circumference - length;
    const rotation = (accumulated / 100) * 360 - 90;
    accumulated += pct;
    return { ...seg, pct, length, gap, rotation };
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="flex flex-col items-center"
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.03)"
            strokeWidth={stroke}
          />
          {segments.map((seg, i) => (
            <circle
              key={seg.key}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={seg.color}
              strokeWidth={stroke}
              strokeDasharray={`${seg.length} ${seg.gap}`}
              transform={`rotate(${seg.rotation} ${size / 2} ${size / 2})`}
              style={{
                transition: `stroke-dasharray 1s cubic-bezier(0.25, 0.46, 0.45, 0.94) ${i * 0.15}s`,
                filter: `drop-shadow(0 0 4px ${seg.color}30)`,
              }}
              strokeLinecap="butt"
            />
          ))}
        </svg>
      </div>

      {/* Legend */}
      <div className="mt-5 flex gap-6">
        {segments.map((seg) => (
          <div key={seg.key} className="flex flex-col items-center">
            <span
              className="text-xl font-semibold font-mono tracking-tight"
              style={{ color: seg.color }}
            >
              {seg.pct}%
            </span>
            <div className="flex items-center gap-1.5 mt-1">
              <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: seg.color }} />
              <span className="text-[10px] text-text-dim uppercase tracking-wider">{seg.label}</span>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
