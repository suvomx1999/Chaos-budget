import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-bg/70 backdrop-blur-xl border-b border-white/[0.04]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-6 h-6 rounded-md bg-primary/15 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-primary shadow-glow-sm" />
          </div>
          <span className="text-sm font-semibold text-text tracking-tight">
            Chaos Budget
          </span>
        </Link>

        <div className="flex items-center gap-5">
          <Link
            to="/input"
            className="text-xs text-text-muted hover:text-text transition-colors"
          >
            Analyze
          </Link>
          <a
            href="https://github.com/suvomx1999/Chaos-budget"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-text-muted hover:text-text transition-colors"
          >
            GitHub
          </a>
        </div>
      </div>
    </nav>
  );
}
