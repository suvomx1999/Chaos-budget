import {
  GraduationCap, Briefcase, Wrench, Trophy, AlertTriangle,
  MapPin, Heart, HelpCircle, Trash2,
} from "lucide-react";
import type { TimelineEvent, EventType } from "../../types";

const EVENT_ICONS: Record<EventType, React.ReactNode> = {
  education: <GraduationCap className="h-3.5 w-3.5" />,
  job: <Briefcase className="h-3.5 w-3.5" />,
  skill: <Wrench className="h-3.5 w-3.5" />,
  achievement: <Trophy className="h-3.5 w-3.5" />,
  failure: <AlertTriangle className="h-3.5 w-3.5" />,
  relocation: <MapPin className="h-3.5 w-3.5" />,
  personal: <Heart className="h-3.5 w-3.5" />,
  other: <HelpCircle className="h-3.5 w-3.5" />,
};

const EVENT_COLORS: Record<EventType, { dot: string; badge: string }> = {
  education: { dot: "bg-blue-400", badge: "text-blue-400 bg-blue-400/[0.08] border-blue-400/20" },
  job: { dot: "bg-emerald-400", badge: "text-emerald-400 bg-emerald-400/[0.08] border-emerald-400/20" },
  skill: { dot: "bg-cyan-400", badge: "text-cyan-400 bg-cyan-400/[0.08] border-cyan-400/20" },
  achievement: { dot: "bg-amber-400", badge: "text-amber-400 bg-amber-400/[0.08] border-amber-400/20" },
  failure: { dot: "bg-red-400", badge: "text-red-400 bg-red-400/[0.08] border-red-400/20" },
  relocation: { dot: "bg-violet-400", badge: "text-violet-400 bg-violet-400/[0.08] border-violet-400/20" },
  personal: { dot: "bg-pink-400", badge: "text-pink-400 bg-pink-400/[0.08] border-pink-400/20" },
  other: { dot: "bg-slate-400", badge: "text-slate-400 bg-slate-400/[0.08] border-slate-400/20" },
};

interface TimelineEventCardProps {
  event: TimelineEvent;
  onDelete?: (id: string) => void;
  onEdit?: (event: TimelineEvent) => void;
  draggable?: boolean;
}

export default function TimelineEventCard({
  event,
  onDelete,
  onEdit,
}: TimelineEventCardProps) {
  const colors = EVENT_COLORS[event.event_type];

  return (
    <div className="group flex items-start gap-3 mb-3">
      {/* Timeline dot + line */}
      <div className="flex flex-col items-center pt-3">
        <div className={`w-2 h-2 rounded-full ${colors.dot} ring-4 ring-bg-card/80`} />
        <div className="w-px flex-1 bg-white/[0.06] mt-1" />
      </div>

      {/* Card */}
      <div
        className="flex-1 bg-white/[0.02] border border-white/[0.06] rounded-xl p-3.5 hover:border-white/[0.10] transition-all cursor-pointer"
        onClick={() => onEdit?.(event)}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-mono text-text-dim">
                {event.year}{event.month ? `/${String(event.month).padStart(2, "0")}` : ""}
              </span>
              <span className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full border ${colors.badge}`}>
                {EVENT_ICONS[event.event_type]}
                {event.event_type}
              </span>
            </div>
            <h4 className="font-medium text-sm text-text">{event.title}</h4>
            {event.organization && (
              <p className="text-xs text-text-muted mt-0.5">{event.organization}</p>
            )}
            {event.description && (
              <p className="text-xs text-text-dim mt-1 line-clamp-2">{event.description}</p>
            )}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <div className="flex flex-col items-center">
              <span className="text-[9px] text-text-dim uppercase tracking-wider">effort</span>
              <span className={`text-xs font-mono font-medium ${
                event.self_rating >= 7 ? "text-emerald-400" :
                event.self_rating >= 4 ? "text-amber-400" : "text-red-400"
              }`}>
                {event.self_rating}/10
              </span>
            </div>

            {onDelete && (
              <button
                onClick={(e) => { e.stopPropagation(); onDelete(event.id); }}
                className="p-1.5 rounded-lg hover:bg-red-500/[0.08] text-text-dim hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                title="Remove event"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
