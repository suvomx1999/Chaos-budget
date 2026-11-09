import { useState } from "react";
import { Plus, X } from "lucide-react";
import { v4 as uuidv4 } from "uuid";
import Button from "../UI/Button";
import TimelineEventCard from "./TimelineEventCard";
import TimelineSummary from "./TimelineSummary";
import type { TimelineEvent, EventType } from "../../types";

const EVENT_TYPES: { value: EventType; label: string }[] = [
  { value: "education", label: "Education" },
  { value: "job", label: "Job / Work" },
  { value: "skill", label: "Skill Building" },
  { value: "achievement", label: "Achievement" },
  { value: "failure", label: "Failure / Setback" },
  { value: "relocation", label: "Relocation" },
  { value: "personal", label: "Personal" },
  { value: "other", label: "Other" },
];

const MONTHS = [
  { value: 0, label: "Not sure" },
  ...Array.from({ length: 12 }, (_, i) => ({
    value: i + 1,
    label: new Date(2000, i).toLocaleString("default", { month: "long" }),
  })),
];

interface TimelineFormProps {
  events: TimelineEvent[];
  onEventsChange: (events: TimelineEvent[]) => void;
}

const emptyEvent = (): Partial<TimelineEvent> => ({
  year: new Date().getFullYear(),
  month: null,
  event_type: "job",
  title: "",
  organization: "",
  description: "",
  self_rating: 5,
  duration_months: undefined,
});

const inputCls =
  "w-full bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-text placeholder-text-dim/40 focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/10 transition-all";

export default function TimelineForm({ events, onEventsChange }: TimelineFormProps) {
  const [showModal, setShowModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState<Partial<TimelineEvent>>(emptyEvent());
  const [editId, setEditId] = useState<string | null>(null);

  const openAdd = () => {
    setEditingEvent(emptyEvent());
    setEditId(null);
    setShowModal(true);
  };

  const openEdit = (event: TimelineEvent) => {
    setEditingEvent({ ...event });
    setEditId(event.id);
    setShowModal(true);
  };

  const handleSave = () => {
    if (!editingEvent.title?.trim() || !editingEvent.year) return;

    const event: TimelineEvent = {
      id: editId || uuidv4(),
      year: editingEvent.year!,
      month: editingEvent.month || null,
      event_type: editingEvent.event_type as EventType || "other",
      title: editingEvent.title!.trim(),
      organization: editingEvent.organization?.trim() || null,
      description: editingEvent.description?.trim() || null,
      self_rating: editingEvent.self_rating || 5,
      duration_months: editingEvent.duration_months || null,
    };

    if (editId) {
      onEventsChange(events.map((e) => (e.id === editId ? event : e)));
    } else {
      onEventsChange([...events, event]);
    }
    setShowModal(false);
  };

  const handleDelete = (id: string) => {
    onEventsChange(events.filter((e) => e.id !== id));
  };

  const sorted = [...events].sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year;
    return (a.month || 0) - (b.month || 0);
  });

  return (
    <div>
      {sorted.length > 0 && <TimelineSummary events={sorted} />}

      {sorted.length > 0 ? (
        <div className="mb-4">
          {sorted.map((event) => (
            <TimelineEventCard
              key={event.id}
              event={event}
              onDelete={handleDelete}
              onEdit={openEdit}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-text-dim">
          <p className="text-sm mb-1">No events yet</p>
          <p className="text-xs text-text-dim/60">Add your first career event below</p>
        </div>
      )}

      <Button variant="secondary" onClick={openAdd} className="w-full">
        <Plus className="h-3.5 w-3.5" />
        Add Event
      </Button>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="glass-strong rounded-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-xl">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-sm font-semibold">
                {editId ? "Edit Event" : "Add Event"}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="p-1 rounded-lg hover:bg-white/[0.04] text-text-dim"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3.5">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] text-text-dim uppercase tracking-wider mb-1">Year *</label>
                  <input
                    type="number"
                    min={1950}
                    max={2030}
                    value={editingEvent.year || ""}
                    onChange={(e) => setEditingEvent({ ...editingEvent, year: parseInt(e.target.value) || undefined })}
                    className={inputCls}
                  />
                </div>
                <div>
                  <label className="block text-[10px] text-text-dim uppercase tracking-wider mb-1">Month</label>
                  <select
                    value={editingEvent.month || 0}
                    onChange={(e) => setEditingEvent({ ...editingEvent, month: parseInt(e.target.value) || null })}
                    className={inputCls}
                  >
                    {MONTHS.map((m) => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[10px] text-text-dim uppercase tracking-wider mb-1">Event Type *</label>
                <select
                  value={editingEvent.event_type || "job"}
                  onChange={(e) => setEditingEvent({ ...editingEvent, event_type: e.target.value as EventType })}
                  className={inputCls}
                >
                  {EVENT_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] text-text-dim uppercase tracking-wider mb-1">Title *</label>
                <input
                  type="text"
                  value={editingEvent.title || ""}
                  onChange={(e) => setEditingEvent({ ...editingEvent, title: e.target.value })}
                  placeholder="e.g. Joined Google as SDE-2"
                  className={inputCls}
                />
              </div>

              <div>
                <label className="block text-[10px] text-text-dim uppercase tracking-wider mb-1">Organization</label>
                <input
                  type="text"
                  value={editingEvent.organization || ""}
                  onChange={(e) => setEditingEvent({ ...editingEvent, organization: e.target.value })}
                  placeholder="e.g. Google, MIT"
                  className={inputCls}
                />
              </div>

              <div>
                <label className="block text-[10px] text-text-dim uppercase tracking-wider mb-1">Description</label>
                <textarea
                  value={editingEvent.description || ""}
                  onChange={(e) => setEditingEvent({ ...editingEvent, description: e.target.value })}
                  placeholder="Brief description..."
                  rows={2}
                  className={`${inputCls} resize-none`}
                />
              </div>

              <div>
                <label className="block text-[10px] text-text-dim uppercase tracking-wider mb-1.5">
                  Your effort — <span className="text-text font-medium">{editingEvent.self_rating}/10</span>
                </label>
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={editingEvent.self_rating || 5}
                  onChange={(e) => setEditingEvent({ ...editingEvent, self_rating: parseInt(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-[9px] text-text-dim/40 mt-0.5">
                  <span>Pure luck</span>
                  <span>All me</span>
                </div>
              </div>

              <div>
                <label className="block text-[10px] text-text-dim uppercase tracking-wider mb-1">Duration (months)</label>
                <input
                  type="number"
                  min={0}
                  value={editingEvent.duration_months ?? ""}
                  onChange={(e) => setEditingEvent({ ...editingEvent, duration_months: parseInt(e.target.value) || undefined })}
                  placeholder="Optional"
                  className={inputCls}
                />
              </div>
            </div>

            <div className="flex gap-2.5 mt-5">
              <Button variant="secondary" onClick={() => setShowModal(false)} className="flex-1">
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={!editingEvent.title?.trim() || !editingEvent.year}
                className="flex-1"
              >
                {editId ? "Save Changes" : "Add Event"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
