/** TypeScript interfaces matching backend Pydantic models exactly. */

export type EventType =
  | "education"
  | "job"
  | "skill"
  | "achievement"
  | "failure"
  | "relocation"
  | "personal"
  | "other";

export type CareerLevel =
  | "student"
  | "junior"
  | "mid"
  | "senior"
  | "lead"
  | "executive";

export interface TimelineEvent {
  id: string;
  year: number;
  month: number | null;
  event_type: EventType;
  title: string;
  organization: string | null;
  description: string | null;
  self_rating: number;
  duration_months: number | null;
}

export interface AlternatePath {
  path_id: string;
  events: Record<string, unknown>[];
  final_outcome: string;
  outcome_level: string;
  divergence_point: string;
}

export interface TimelineInput {
  user_id: string;
  raw_text: string | null;
  events: TimelineEvent[] | null;
  current_role: string;
  current_level: CareerLevel;
  field: string;
}

export interface SimulationResult {
  user_id: string;
  chaos_coefficient: number;
  skill_percentage: number;
  luck_percentage: number;
  timing_percentage: number;
  alternate_paths: AlternatePath[];
  key_pivot_events: string[];
  causal_confidence: number | null;
  created_at: string;
}

export interface ExplanationResponse {
  user_id: string;
  chaos_story: string;
  what_skill_built: string;
  what_luck_shaped: string;
  alternate_you: string;
  surgery_suggestion: string;
}

export interface ParseTextResponse {
  events: TimelineEvent[];
  event_count: number;
}

export interface SubmitResponse {
  user_id: string;
  event_count: number;
  status: string;
}

export interface HealthResponse {
  status: string;
  db: string;
  version: string;
}

export interface CreateSessionResponse {
  session_id: string;
  checkout_url: string;
}

export interface PaymentStatus {
  user_id: string;
  paid: boolean;
  session_id: string | null;
}
