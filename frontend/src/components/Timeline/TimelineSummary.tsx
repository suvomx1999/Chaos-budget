import type { TimelineEvent, EventType } from "../../types";

const TYPE_LABELS: Record<EventType, string> = {
  education: "education",
  job: "jobs",
  skill: "skills",
  achievement: "achievements",
  failure: "setbacks",
  relocation: "moves",
  personal: "personal",
  other: "other",
};

function buildArc(events: TimelineEvent[]): string {
  const sorted = [...events].sort((a, b) => a.year - b.year);
  const first = sorted[0];
  const last = sorted[sorted.length - 1];
  const span = last.year - first.year;
  const jobs = sorted.filter((e) => e.event_type === "job");
  const setbacks = sorted.filter((e) => e.event_type === "failure");
  const avgEffort =
    sorted.reduce((s, e) => s + e.self_rating, 0) / sorted.length;

  const start = first.organization || first.title;
  const end = last.organization || last.title;
  const years = span <= 0 ? "the same year" : `${span} year${span === 1 ? "" : "s"}`;

  let arc = `Your path runs ${years}, from ${start} to ${end}.`;
  if (jobs.length > 0) {
    arc += ` ${jobs.length} role${jobs.length === 1 ? "" : "s"} on record.`;
  }
  if (setbacks.length > 0) {
    arc += ` ${setbacks.length} setback${setbacks.length === 1 ? "" : "s"} may be a pivot.`;
  }
  if (avgEffort >= 7.5) {
    arc += " You rated most of this as your own effort.";
  } else if (avgEffort <= 4) {
    arc += " You rated a lot of this as outside your control.";
  }

  return arc;
}

interface TimelineSummaryProps {
  events: TimelineEvent[];
}

export default function TimelineSummary({ events }: TimelineSummaryProps) {
  if (events.length === 0) return null;

  const years = events.map((e) => e.year);
  const minYear = Math.min(...years);
  const maxYear = Math.max(...years);
  const avgEffort =
    events.reduce((s, e) => s + e.self_rating, 0) / events.length;

  const counts = events.reduce<Partial<Record<EventType, number>>>((acc, e) => {
    acc[e.event_type] = (acc[e.event_type] || 0) + 1;
    return acc;
  }, {});

  const breakdown = (Object.entries(counts) as [EventType, number][])
    .sort((a, b) => b[1] - a[1])
    .map(([type, n]) => `${n} ${TYPE_LABELS[type]}`)
    .join(" · ");

  return (
    <div className="mb-5 rounded-xl border border-primary/15 bg-primary/[0.04] p-4">
      <p className="text-[10px] uppercase tracking-wider text-primary mb-2">
        Timeline summary
      </p>
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-2">
        <span className="font-mono text-lg text-text">
          {minYear === maxYear ? minYear : `${minYear}–${maxYear}`}
        </span>
        <span className="text-xs text-text-muted">
          {events.length} event{events.length === 1 ? "" : "s"}
        </span>
        <span className="text-xs text-text-dim">
          avg effort {avgEffort.toFixed(1)}/10
        </span>
      </div>
      <p className="text-xs text-text-muted mb-2">{breakdown}</p>
      <p className="text-sm text-text/90 leading-relaxed">{buildArc(events)}</p>
    </div>
  );
}
