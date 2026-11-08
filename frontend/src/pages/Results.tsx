/**
 * Results page — simulation pipeline + Stripe paywall.
 *
 * Free tier: ChaosScore + SkillLuckPie (visible)
 * Paid tier: AlternatePathsViz + NarrativeExplanation (unlocked after ₹99 payment)
 */

import { useEffect, useState, useCallback } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, Share2, RotateCcw, CheckCircle, Lock } from "lucide-react";

import ChaosScore from "../components/Results/ChaosScore";
import SkillLuckPie from "../components/Results/SkillLuckPie";
import AlternatePathsViz from "../components/Results/AlternatePathsViz";
import NarrativeExplanation from "../components/Results/NarrativeExplanation";
import Button from "../components/UI/Button";
import Card from "../components/UI/Card";
import Loader from "../components/UI/Loader";
import ProgressBar from "../components/UI/ProgressBar";

import {
  runSimulation,
  generateExplanation,
  createPaymentSession,
  getPaymentStatus,
  verifyPaymentSession,
} from "../services/api";
import type { SimulationResult, ExplanationResponse } from "../types";

const STAGES = [
  { key: "sim", label: "Running 1,000 Monte Carlo simulations…" },
  { key: "causal", label: "Applying causal inference…" },
  { key: "explain", label: "Generating AI narrative…" },
  { key: "done", label: "Done!" },
] as const;

type Stage = (typeof STAGES)[number]["key"];

export default function Results() {
  const { userId } = useParams<{ userId: string }>();
  const [searchParams] = useSearchParams();

  const [stage, setStage] = useState<Stage>("sim");
  const [progress, setProgress] = useState(0);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Payment state
  const [paid, setPaid] = useState(false);
  const [paymentLoading, setPaymentLoading] = useState(false);
  const [paymentChecked, setPaymentChecked] = useState(false);

  // Check payment on mount + verify Stripe redirect
  useEffect(() => {
    if (!userId) return;

    const checkPayment = async () => {
      // If returning from Stripe Checkout, verify the session
      const sessionId = searchParams.get("session_id");
      if (sessionId) {
        try {
          const result = await verifyPaymentSession(sessionId);
          if (result.paid) {
            setPaid(true);
            setPaymentChecked(true);
            return;
          }
        } catch {
          // verification failed, fall through to status check
        }
      }

      // Check existing payment status
      try {
        const status = await getPaymentStatus(userId);
        setPaid(status.paid);
      } catch {
        // No payment record yet — that's fine
      }
      setPaymentChecked(true);
    };

    checkPayment();
  }, [userId, searchParams]);

  // Run pipeline
  const runPipeline = useCallback(async () => {
    if (!userId) return;

    setError(null);
    setStage("sim");
    setProgress(10);
    setSimResult(null);
    setExplanation(null);

    try {
      setProgress(20);
      const sim = await runSimulation(userId);
      setSimResult(sim);
      setProgress(50);

      setStage("causal");
      setProgress(60);

      setStage("explain");
      setProgress(70);
      const exp = await generateExplanation(userId);
      setExplanation(exp);

      setStage("done");
      setProgress(100);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Something went wrong. Try again.";
      setError(msg);
    }
  }, [userId]);

  useEffect(() => {
    runPipeline();
  }, [runPipeline]);

  // Payment handler
  const handleUnlock = async () => {
    if (!userId) return;
    setPaymentLoading(true);

    try {
      const currentUrl = window.location.origin;
      const result = await createPaymentSession(
        userId,
        `${currentUrl}/results/${userId}`,
        `${currentUrl}/results/${userId}`
      );

      if (result.checkout_url) {
        // Redirect to Stripe Checkout
        window.location.href = result.checkout_url;
      } else {
        // Already paid
        setPaid(true);
        setPaymentLoading(false);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Payment failed. Try again.";
      setError(msg);
      setPaymentLoading(false);
    }
  };

  // Share handler
  const handleShare = async () => {
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      if (navigator.share) {
        await navigator.share({
          title: "My Chaos Budget",
          text: `My career is ${simResult ? Math.round(simResult.chaos_coefficient * 100) : "?"}% chaos.`,
          url,
        });
      }
    }
  };

  // ─── Loading / Error ─────────────────────────────────────────
  if (!simResult || !explanation) {
    const currentStage = STAGES.find((s) => s.key === stage);

    if (error) {
      return (
        <div className="min-h-screen pt-24 px-4">
          <div className="max-w-md mx-auto text-center">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-danger/[0.08] flex items-center justify-center">
              <span className="text-danger text-lg">!</span>
            </div>
            <h2 className="text-lg font-semibold mb-2">Analysis Failed</h2>
            <p className="text-sm text-text-muted mb-6">{error}</p>
            <div className="flex gap-2.5 justify-center">
              <Button onClick={runPipeline} size="sm">
                <RotateCcw className="h-3.5 w-3.5" />
                Retry
              </Button>
              <Link to="/input">
                <Button variant="secondary" size="sm">
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Back
                </Button>
              </Link>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen pt-24 px-4">
        <div className="max-w-sm mx-auto">
          <Card className="text-center">
            <Loader
              message={currentStage?.label || "Processing..."}
              size="lg"
            />
            <div className="mt-5 px-4">
              <ProgressBar progress={progress} />
            </div>
            <div className="mt-4 flex justify-center gap-1.5">
              {STAGES.slice(0, -1).map((s) => (
                <div
                  key={s.key}
                  className={`w-2 h-2 rounded-full transition-colors duration-500 ${
                    STAGES.findIndex((x) => x.key === s.key) <=
                    STAGES.findIndex((x) => x.key === stage)
                      ? "bg-primary"
                      : "bg-white/[0.06]"
                  }`}
                />
              ))}
            </div>
          </Card>
        </div>
      </div>
    );
  }

  // ─── Dashboard ───────────────────────────────────────────────
  const showLocked = paymentChecked && !paid;

  return (
    <div className="min-h-screen pt-20 pb-16 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <Link
              to="/input"
              className="text-text-dim hover:text-text-muted text-xs flex items-center gap-1 mb-1.5 transition-colors"
            >
              <ArrowLeft className="h-3 w-3" />
              New analysis
            </Link>
            <h1 className="text-2xl font-semibold tracking-tight">Your Chaos Budget</h1>
          </div>
          <Button variant="secondary" size="sm" onClick={handleShare}>
            {copied ? (
              <>
                <CheckCircle className="h-3.5 w-3.5 text-success" />
                Copied
              </>
            ) : (
              <>
                <Share2 className="h-3.5 w-3.5" />
                Share
              </>
            )}
          </Button>
        </motion.div>

        {/* ── FREE TIER: Score + Pie ─────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Card className="flex items-center justify-center py-8">
            <ChaosScore
              value={simResult.chaos_coefficient}
              causalConfidence={simResult.causal_confidence}
            />
          </Card>
          <Card className="flex items-center justify-center py-8">
            <SkillLuckPie
              skill={simResult.skill_percentage}
              luck={simResult.luck_percentage}
              timing={simResult.timing_percentage}
            />
          </Card>
        </div>

        {/* ── PAYWALL ────────────────────────────────────────── */}
        {showLocked && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="mb-6"
          >
            <div className="relative rounded-2xl overflow-hidden">
              {/* Blurred preview of locked content */}
              <div className="blur-md opacity-40 pointer-events-none select-none p-6">
                <h2 className="text-sm font-semibold mb-3 text-text-muted uppercase tracking-wider">
                  Alternate Career Paths
                </h2>
                <div className="bg-bg-card/60 rounded-xl p-4 mb-4">
                  <div className="space-y-2">
                    <div className="h-4 bg-white/[0.04] rounded w-3/4" />
                    <div className="h-4 bg-white/[0.04] rounded w-1/2" />
                    <div className="h-4 bg-white/[0.04] rounded w-2/3" />
                  </div>
                </div>
                <h2 className="text-sm font-semibold mb-3 text-text-muted uppercase tracking-wider">
                  AI Narrative
                </h2>
                <div className="bg-bg-card/60 rounded-xl p-4">
                  <div className="space-y-2">
                    <div className="h-4 bg-white/[0.04] rounded w-full" />
                    <div className="h-4 bg-white/[0.04] rounded w-5/6" />
                    <div className="h-4 bg-white/[0.04] rounded w-4/5" />
                    <div className="h-4 bg-white/[0.04] rounded w-3/4" />
                  </div>
                </div>
              </div>

              {/* Unlock overlay */}
              <div className="absolute inset-0 flex items-center justify-center bg-bg/60 backdrop-blur-sm">
                <div className="text-center max-w-sm px-4">
                  <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-primary/[0.08] border border-primary/[0.15] flex items-center justify-center">
                    <Lock className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Unlock Full Analysis</h3>
                  <p className="text-sm text-text-muted mb-1">
                    Get AI narrative, alternate career paths, and chaos surgery suggestion
                  </p>
                  <p className="text-xs text-text-dim mb-5">
                    One-time payment · Instant access
                  </p>
                  <Button
                    size="lg"
                    onClick={handleUnlock}
                    loading={paymentLoading}
                    className="w-full max-w-xs"
                  >
                    Unlock for ₹99
                  </Button>
                  <p className="text-[10px] text-text-dim mt-3">
                    Powered by Stripe · Secure payment
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* ── PAID TIER: Alternate Paths + Narrative ──────────── */}
        {paid && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="mb-6"
            >
              <h2 className="text-sm font-semibold mb-3 text-text-muted uppercase tracking-wider">
                Alternate Career Paths
              </h2>
              <Card>
                <AlternatePathsViz
                  paths={simResult.alternate_paths}
                  pivotEvents={simResult.key_pivot_events}
                />
              </Card>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mb-6"
            >
              <h2 className="text-sm font-semibold mb-3 text-text-muted uppercase tracking-wider">
                AI Narrative
              </h2>
              <NarrativeExplanation
                chaos_story={explanation.chaos_story}
                what_skill_built={explanation.what_skill_built}
                what_luck_shaped={explanation.what_luck_shaped}
                alternate_you={explanation.alternate_you}
                surgery_suggestion={explanation.surgery_suggestion}
              />
            </motion.div>
          </>
        )}

        {/* Footer CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="text-center pt-4"
        >
          <p className="text-xs text-text-dim mb-3">
            Want to explore a different timeline?
          </p>
          <Link to="/input">
            <Button variant="secondary" size="sm">
              <RotateCcw className="h-3.5 w-3.5" />
              Analyze Another Career
            </Button>
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
