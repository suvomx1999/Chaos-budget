import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { v4 as uuidv4 } from "uuid";
import { PenLine, FileText, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Button from "../components/UI/Button";
import Loader from "../components/UI/Loader";
import Card from "../components/UI/Card";
import TimelineForm from "../components/Timeline/TimelineForm";
import TimelineEventCard from "../components/Timeline/TimelineEventCard";
import TimelineSummary from "../components/Timeline/TimelineSummary";
import TextPasteInput from "../components/Timeline/TextPasteInput";
import { submitTimeline } from "../services/api";
import type { TimelineEvent, CareerLevel } from "../types";

const CAREER_LEVELS: { value: CareerLevel; label: string }[] = [
  { value: "student", label: "Student" },
  { value: "junior", label: "Junior" },
  { value: "mid", label: "Mid-level" },
  { value: "senior", label: "Senior" },
  { value: "lead", label: "Lead" },
  { value: "executive", label: "Executive" },
];

type Tab = "form" | "paste";

function inferProfile(events: TimelineEvent[]): {
  role: string;
  field: string;
  level: CareerLevel;
} {
  const sorted = [...events].sort(
    (a, b) => a.year - b.year || (a.month || 0) - (b.month || 0)
  );
  const jobs = sorted.filter((e) => e.event_type === "job");
  const lastJob = jobs.at(-1);
  const last = sorted.at(-1);

  const blob = events
    .map((e) => `${e.title} ${e.organization ?? ""} ${e.description ?? ""}`)
    .join(" ")
    .toLowerCase();

  const stillStudying = sorted.some((e) => e.event_type === "education");
  const hasEmployerJob = jobs.some(
    (e) => e.organization && !/project|hackathon|personal/i.test(`${e.title} ${e.organization}`)
  );

  const edu = [...sorted].reverse().find((e) => e.event_type === "education");
  let role = "";
  if (stillStudying && !hasEmployerJob && edu) {
    role = edu.organization
      ? `Student · ${edu.organization}`
      : edu.title;
  } else if (lastJob) {
    role = lastJob.organization
      ? `${lastJob.title} · ${lastJob.organization}`
      : lastJob.title;
  } else {
    role = last?.title || "";
  }

  // CS/engineering keywords beat incidental "clinical"/"medical" project titles
  let field = "";
  if (/computer|software|cse|\bcs\b|machine learning|\bml\b|\bai\b|data sci|full.?stack/.test(blob)) {
    field = "software engineering";
  } else if (/medic|mbbs|doctor|nurs|pharmacy/.test(blob)) field = "medicine";
  else if (/financ|bank|chartered accountant|\bca\b/.test(blob)) field = "finance";
  else if (/\blaw\b|legal|advocate/.test(blob)) field = "law";
  else if (/\bmba\b|consulting|management/.test(blob)) field = "management";
  else if (/phd|professor|academia|research scholar/.test(blob)) field = "academia";

  let level: CareerLevel = "student";
  if (/executive|director|vp\b/.test(blob)) level = "executive";
  else if (/lead|principal|staff/.test(blob)) level = "lead";
  else if (/senior|sde-?2|sde-?3/.test(blob)) level = "senior";
  else if (jobs.length >= 2) level = "mid";
  else if (jobs.length >= 1) level = "junior";

  if (stillStudying && !hasEmployerJob) level = "student";

  return { role, field, level };
}

export default function Input() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [activeTab, setActiveTab] = useState<Tab>(
    (searchParams.get("tab") as Tab) || "paste"
  );
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [parsedEvents, setParsedEvents] = useState<TimelineEvent[] | null>(null);
  const [currentRole, setCurrentRole] = useState("");
  const [currentLevel, setCurrentLevel] = useState<CareerLevel>("mid");
  const [field, setField] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEventsParsed = (parsed: TimelineEvent[]) => {
    setParsedEvents(parsed);
  };

  const confirmParsedEvents = () => {
    if (!parsedEvents) return;
    const inferred = inferProfile(parsedEvents);
    setEvents(parsedEvents);
    setParsedEvents(null);
    setActiveTab("form");
    setCurrentRole((prev) => prev.trim() || inferred.role);
    setField((prev) => prev.trim() || inferred.field);
    setCurrentLevel(inferred.level);
  };

  const editParsedEvent = (updated: TimelineEvent) => {
    if (parsedEvents) {
      setParsedEvents(parsedEvents.map((e) => (e.id === updated.id ? updated : e)));
    }
  };

  const deleteParsedEvent = (id: string) => {
    if (parsedEvents) {
      setParsedEvents(parsedEvents.filter((e) => e.id !== id));
    }
  };

  const handleSubmit = async () => {
    if (events.length === 0) {
      setError("Add at least one timeline event.");
      return;
    }
    if (!currentRole.trim()) {
      setError("Enter your current role.");
      return;
    }
    if (!field.trim()) {
      setError("Enter your field of work.");
      return;
    }

    setError(null);
    setSubmitting(true);
    const userId = uuidv4();

    try {
      await submitTimeline({
        user_id: userId,
        events,
        current_role: currentRole,
        current_level: currentLevel,
        field,
      });
      navigate(`/results/${userId}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to submit. Try again.";
      setError(msg);
      setSubmitting(false);
    }
  };

  useEffect(() => { window.scrollTo(0, 0); }, []);

  // If events already exist (e.g. after confirm) but profile is blank, infer it.
  useEffect(() => {
    if (events.length === 0) return;
    if (currentRole.trim() && field.trim()) return;
    const inferred = inferProfile(events);
    if (!currentRole.trim() && inferred.role) setCurrentRole(inferred.role);
    if (!field.trim() && inferred.field) setField(inferred.field);
    setCurrentLevel(inferred.level);
  }, [events]); // eslint-disable-line react-hooks/exhaustive-deps

  if (submitting) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader message="Saving your timeline..." size="lg" />
      </div>
    );
  }

  const inputCls =
    "w-full bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2.5 text-sm text-text placeholder-text-dim/50 focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/10 transition-all";

  return (
    <div className="min-h-screen pt-20 pb-16 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-2xl font-semibold tracking-tight">Build Your Timeline</h1>
          <p className="text-sm text-text-muted mt-1">
            Add events manually or let AI extract them from your resume
          </p>
        </motion.div>

        {/* Tabs */}
        {!parsedEvents && (
          <div className="flex bg-white/[0.02] rounded-xl p-1 mb-5 border border-white/[0.06]">
            <button
              onClick={() => setActiveTab("form")}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium transition-all ${
                activeTab === "form"
                  ? "bg-primary/15 text-primary border border-primary/20"
                  : "text-text-muted hover:text-text border border-transparent"
              }`}
            >
              <PenLine className="h-3.5 w-3.5" />
              Build Timeline
            </button>
            <button
              onClick={() => setActiveTab("paste")}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-medium transition-all ${
                activeTab === "paste"
                  ? "bg-primary/15 text-primary border border-primary/20"
                  : "text-text-muted hover:text-text border border-transparent"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              Paste Resume
            </button>
          </div>
        )}

        {/* Parsed events review mode */}
        {parsedEvents && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className="mb-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-base font-semibold">
                    Review Extracted Events
                  </h2>
                  <p className="text-xs text-text-muted mt-0.5">
                    {parsedEvents.length} events found — edit or remove before continuing
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setParsedEvents(null)}
                >
                  ← Back
                </Button>
              </div>

              <TimelineSummary events={parsedEvents} />

              {parsedEvents.map((event) => (
                <TimelineEventCard
                  key={event.id}
                  event={event}
                  onDelete={deleteParsedEvent}
                  onEdit={editParsedEvent}
                />
              ))}

              <Button onClick={confirmParsedEvents} className="w-full mt-4">
                Confirm {parsedEvents.length} Events & Continue
                <ChevronRight className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </Card>
          </motion.div>
        )}

        {/* Profile + submit sit ABOVE the long timeline so they aren't missed */}
        {events.length > 0 && !parsedEvents && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className="mb-5">
              <h3 className="text-sm font-semibold mb-4 text-text-muted uppercase tracking-wider">
                About You
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-text-dim mb-1">Current Role *</label>
                  <input
                    type="text"
                    value={currentRole}
                    onChange={(e) => setCurrentRole(e.target.value)}
                    placeholder="e.g. Senior SDE-2, Product Manager"
                    className={inputCls}
                  />
                </div>

                <div>
                  <label className="block text-xs text-text-dim mb-1">Current Level *</label>
                  <select
                    value={currentLevel}
                    onChange={(e) => setCurrentLevel(e.target.value as CareerLevel)}
                    className={inputCls}
                  >
                    {CAREER_LEVELS.map((l) => (
                      <option key={l.value} value={l.value}>{l.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-text-dim mb-1">Field of Work *</label>
                  <input
                    type="text"
                    value={field}
                    onChange={(e) => setField(e.target.value)}
                    placeholder="e.g. software engineering, medicine, finance"
                    className={inputCls}
                  />
                </div>
              </div>
            </Card>

            <Button
              size="lg"
              onClick={handleSubmit}
              disabled={events.length === 0 || !currentRole.trim() || !field.trim()}
              className="w-full mb-5"
            >
              Analyze My Chaos Budget
              <ChevronRight className="h-4 w-4" />
            </Button>
            {(!currentRole.trim() || !field.trim()) && (
              <p className="-mt-3 mb-5 text-xs text-warning text-center">
                Fill current role and field of work, then tap Analyze to see your results.
              </p>
            )}
          </motion.div>
        )}

        {/* Tab content */}
        {!parsedEvents && (
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: activeTab === "form" ? -16 : 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: activeTab === "form" ? 16 : -16 }}
              transition={{ duration: 0.2 }}
            >
              <Card className="mb-5">
                {activeTab === "form" ? (
                  <TimelineForm events={events} onEventsChange={setEvents} />
                ) : (
                  <TextPasteInput onEventsParsed={handleEventsParsed} />
                )}
              </Card>
            </motion.div>
          </AnimatePresence>
        )}

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-danger/[0.08] border border-danger/20 text-danger text-xs">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
