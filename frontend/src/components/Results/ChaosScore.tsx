/**
 * ChaosScore — animated SVG ring gauge showing the Chaos Coefficient.
 * Sleek dark dashboard style with teal/amber/red accent based on score.
 */

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface ChaosScoreProps {
  value: number; // 0-1
  causalConfidence: number | null;
}

function interpretScore(v: number): { label: string; color: string } {
  if (v >= 0.7) return { label: "Heavily luck-driven", color: "#ef4444" };
  if (v >= 0.5) return { label: "Luck slightly wins", color: "#f59e0b" };
  if (v >= 0.35) return { label: "Balanced mix", color: "#3b82f6" };
  if (v >= 0.2) return { label: "Skill slightly wins", color: "#06b6d4" };
  return { label: "Strongly skill-driven", color: "#10b981" };
}

export default function ChaosScore({ value, causalConfidence }: ChaosScoreProps) {
  const [animatedValue, setAnimatedValue] = useState(0);

  useEffect(() => {
    const duration = 1800;
    const start = performance.now();
    const target = Math.round(value * 100);

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedValue(Math.round(target * eased));
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }, [value]);

  const { label, color } = interpretScore(value);

  const size = 200;
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - value);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" as const }}
      className="flex flex-col items-center"
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.03)"
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              transition: "stroke-dashoffset 1.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
              filter: `drop-shadow(0 0 6px ${color}40)`,
            }}
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-semibold tracking-tight" style={{ color }}>
            {animatedValue}
          </span>
          <span className="text-[10px] text-text-dim font-mono mt-0.5">/ 100</span>
        </div>
      </div>

      <p className="mt-3 text-sm font-medium" style={{ color }}>
        {label}
      </p>
      <p className="text-[10px] text-text-dim mt-0.5 uppercase tracking-wider">
        Chaos Coefficient
      </p>

      {causalConfidence !== null && (
        <div className="mt-3 px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.06]">
          <span className="text-[10px] text-text-dim">
            Causal confidence:{" "}
            <span className="text-text-muted font-mono">{(causalConfidence * 100).toFixed(0)}%</span>
          </span>
        </div>
      )}
    </motion.div>
  );
}
