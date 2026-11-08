export default function Footer() {
  return (
    <footer className="border-t border-white/[0.04] py-6 mt-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p className="text-xs text-text-dim">
          Chaos Budget — Counterfactual career simulation
        </p>
        <p className="text-xs text-text-dim/60">
          FastAPI · React · DoWhy · Groq
        </p>
      </div>
    </footer>
  );
}
