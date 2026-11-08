import { useNavigate } from "react-router-dom";
import { ArrowRight, FileText, Dice5, Brain, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";
import Button from "../components/UI/Button";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.12, duration: 0.6, ease: "easeOut" as const },
  }),
};

const features = [
  {
    icon: Dice5,
    title: "Monte Carlo Engine",
    desc: "1,000 counterfactual career paths simulated at every pivot point in your timeline.",
    color: "#00d4aa",
  },
  {
    icon: Brain,
    title: "Causal Inference",
    desc: "DoWhy-powered estimation separating genuine skill impact from circumstantial luck.",
    color: "#3b82f6",
  },
  {
    icon: TrendingUp,
    title: "AI Narrative",
    desc: "LLM-generated analysis of your story — what you built, what luck shaped, and the alternate you.",
    color: "#f59e0b",
  },
];

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-4 pt-24 pb-16">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <span className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-primary/[0.08] border border-primary/[0.15] text-xs text-primary font-medium tracking-wide">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-glow-pulse" />
            Monte Carlo · Causal Inference · LLM
          </span>
        </motion.div>

        <motion.h1
          custom={0}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="text-4xl sm:text-5xl md:text-6xl font-semibold leading-[1.1] max-w-3xl tracking-tight"
        >
          How much of your career{" "}
          <span className="text-primary">is really you?</span>
        </motion.h1>

        <motion.p
          custom={1}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mt-6 text-base sm:text-lg text-text-muted max-w-xl leading-relaxed font-light"
        >
          Simulate 1,000 alternate versions of your career to measure
          skill vs. luck vs. timing. Math, counterfactuals, honest analysis.
        </motion.p>

        <motion.div
          custom={2}
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="mt-10 flex flex-col sm:flex-row gap-3"
        >
          <Button size="lg" onClick={() => navigate("/input?tab=form")}>
            Enter my timeline
            <ArrowRight className="h-4 w-4" />
          </Button>
          <Button
            variant="secondary"
            size="lg"
            onClick={() => navigate("/input?tab=paste")}
          >
            <FileText className="h-4 w-4" />
            Paste my resume
          </Button>
        </motion.div>
      </section>

      {/* Feature cards */}
      <section className="max-w-4xl mx-auto px-4 pb-20 grid grid-cols-1 md:grid-cols-3 gap-4">
        {features.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              custom={i + 3}
              variants={fadeUp}
              initial="hidden"
              animate="visible"
              className="bg-bg-card/40 backdrop-blur-sm border border-white/[0.06] rounded-2xl p-5 hover:border-white/[0.10] transition-all duration-300 card-glow"
            >
              <div
                className="w-9 h-9 rounded-lg flex items-center justify-center mb-4"
                style={{ backgroundColor: `${card.color}12` }}
              >
                <Icon className="h-4.5 w-4.5" style={{ color: card.color }} />
              </div>
              <h3 className="text-sm font-semibold mb-1.5 text-text">{card.title}</h3>
              <p className="text-xs text-text-muted leading-relaxed">
                {card.desc}
              </p>
            </motion.div>
          );
        })}
      </section>
    </div>
  );
}
