/**
 * NarrativeExplanation — 4-part AI story + surgery suggestion.
 * Clean, minimal card style matching the dashboard aesthetic.
 */

import { motion } from "framer-motion";
import { BookOpen, Wrench, Sparkles, Users, Scissors } from "lucide-react";
import type { ExplanationResponse } from "../../types";

type NarrativeExplanationProps = Omit<ExplanationResponse, "user_id"> & {
  /** "story" = free teaser (Chaos Story only). "full" = all sections. */
  variant?: "story" | "full";
};

const SECTIONS = [
  {
    key: "chaos_story" as const,
    title: "Your Chaos Story",
    subtitle: "How chaos shaped your career",
    icon: BookOpen,
    color: "#06b6d4",
  },
  {
    key: "what_skill_built" as const,
    title: "What Skill Built",
    subtitle: "Foundations from deliberate effort",
    icon: Wrench,
    color: "#10b981",
  },
  {
    key: "what_luck_shaped" as const,
    title: "What Luck Shaped",
    subtitle: "Twists of fortune that altered your path",
    icon: Sparkles,
    color: "#f59e0b",
  },
  {
    key: "alternate_you" as const,
    title: "The Alternate You",
    subtitle: "A parallel universe version",
    icon: Users,
    color: "#3b82f6",
  },
];

export default function NarrativeExplanation({
  variant = "full",
  ...props
}: NarrativeExplanationProps) {
  const visible = variant === "story"
    ? SECTIONS.filter((s) => s.key === "chaos_story")
    : SECTIONS;

  return (
    <div className="space-y-3">
      {visible.map((section, i) => {
        const Icon = section.icon;
        const text = props[section.key];
        if (!text) return null;

        return (
          <motion.div
            key={section.key}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.12 * i }}
            className="bg-white/[0.02] border border-white/[0.05] rounded-xl p-4 hover:border-white/[0.08] transition-colors"
          >
            <div className="flex items-center gap-2.5 mb-3">
              <div
                className="w-7 h-7 rounded-md flex items-center justify-center"
                style={{ backgroundColor: `${section.color}10` }}
              >
                <Icon className="h-3.5 w-3.5" style={{ color: section.color }} />
              </div>
              <div>
                <h4 className="text-xs font-medium text-text">{section.title}</h4>
                <p className="text-[10px] text-text-dim">{section.subtitle}</p>
              </div>
            </div>
            <p className="text-sm text-text-muted leading-relaxed whitespace-pre-line">
              {text}
            </p>
          </motion.div>
        );
      })}

      {/* Surgery Suggestion — paid only */}
      {variant === "full" && props.surgery_suggestion && (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.6 }}
          className="bg-primary/[0.04] border border-primary/[0.10] rounded-xl p-4"
        >
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-7 h-7 rounded-md flex items-center justify-center bg-primary/[0.08]">
              <Scissors className="h-3.5 w-3.5 text-primary" />
            </div>
            <div>
              <h4 className="text-xs font-medium text-text">Chaos Surgery</h4>
              <p className="text-[10px] text-text-dim">One change to shift your chaos budget</p>
            </div>
          </div>
          <p className="text-sm text-text-muted leading-relaxed italic">
            &ldquo;{props.surgery_suggestion}&rdquo;
          </p>
        </motion.div>
      )}
    </div>
  );
}
