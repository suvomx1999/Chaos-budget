/**
 * API service — typed async functions for every backend endpoint.
 *
 * In development, Vite proxies /api → http://localhost:8000.
 * In production, set VITE_API_BASE_URL to the Render backend URL.
 */

import axios from "axios";
import type {
  CreateSessionResponse,
  ExplanationResponse,
  HealthResponse,
  ParseTextResponse,
  PaymentStatus,
  SimulationResult,
  SubmitResponse,
  TimelineInput,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 60000, // 60s — simulations + Groq calls can take time
  headers: { "Content-Type": "application/json" },
});

/** Health check */
export async function getHealth(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>("/health");
  return data;
}

/** Parse raw text into structured events */
export async function parseText(rawText: string): Promise<ParseTextResponse> {
  const { data } = await api.post<ParseTextResponse>("/timeline/parse-text", {
    raw_text: rawText,
  });
  return data;
}

/** Upload a PDF resume and parse into events */
export async function parsePdf(file: File): Promise<ParseTextResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<ParseTextResponse>(
    "/timeline/parse-pdf",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

/** Submit a full timeline to MongoDB */
export async function submitTimeline(
  input: Omit<TimelineInput, "raw_text"> & { raw_text?: string | null }
): Promise<SubmitResponse> {
  const { data } = await api.post<SubmitResponse>("/timeline/submit", input);
  return data;
}

/** Get a saved timeline */
export async function getTimeline(userId: string): Promise<TimelineInput> {
  const { data } = await api.get<TimelineInput>(`/timeline/${userId}`);
  return data;
}

/** Run Monte Carlo simulation */
export async function runSimulation(
  userId: string
): Promise<SimulationResult> {
  const { data } = await api.post<SimulationResult>("/simulate", {
    user_id: userId,
  });
  return data;
}

/** Get saved simulation result */
export async function getSimulation(
  userId: string
): Promise<SimulationResult> {
  const { data } = await api.get<SimulationResult>(`/simulate/${userId}`);
  return data;
}

/** Generate narrative explanation */
export async function generateExplanation(
  userId: string
): Promise<ExplanationResponse> {
  const { data } = await api.post<ExplanationResponse>("/explain", {
    user_id: userId,
  });
  return data;
}

/** Get saved explanation */
export async function getExplanation(
  userId: string
): Promise<ExplanationResponse> {
  const { data } = await api.get<ExplanationResponse>(`/explain/${userId}`);
  return data;
}

/** Create a Stripe Checkout session */
export async function createPaymentSession(
  userId: string,
  successUrl: string,
  cancelUrl: string
): Promise<CreateSessionResponse> {
  const { data } = await api.post<CreateSessionResponse>(
    "/payment/create-session",
    { user_id: userId, success_url: successUrl, cancel_url: cancelUrl }
  );
  return data;
}

/** Check payment status for a user */
export async function getPaymentStatus(userId: string): Promise<PaymentStatus> {
  const { data } = await api.get<PaymentStatus>(`/payment/status/${userId}`);
  return data;
}

/** Verify a Stripe Checkout session after redirect */
export async function verifyPaymentSession(
  sessionId: string
): Promise<PaymentStatus> {
  const { data } = await api.post<PaymentStatus>("/payment/verify-session", {
    session_id: sessionId,
  });
  return data;
}
