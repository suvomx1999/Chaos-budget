/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: "#00d4aa", light: "#33e0be", dark: "#00b894" },
        accent: { DEFAULT: "#3b82f6", light: "#60a5fa", warm: "#f59e0b" },
        bg: {
          DEFAULT: "#060a13",
          surface: "#0c1220",
          card: "#111827",
          "card-hover": "#1a2332",
          elevated: "#1e293b",
        },
        text: { DEFAULT: "#e1e7ef", muted: "#64748b", dim: "#475569" },
        border: { DEFAULT: "rgba(255,255,255,0.06)", light: "rgba(255,255,255,0.10)" },
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
        cyan: { DEFAULT: "#06b6d4", light: "#22d3ee" },
      },
      fontFamily: {
        sans: ['"Inter"', "system-ui", "-apple-system", "sans-serif"],
        mono: ['"JetBrains Mono"', '"Fira Code"', "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(0, 212, 170, 0.15)",
        "glow-sm": "0 0 10px rgba(0, 212, 170, 0.10)",
        "glow-accent": "0 0 20px rgba(59, 130, 246, 0.15)",
        card: "0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow-pulse": "glowPulse 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glowPulse: {
          "0%": { opacity: "0.4" },
          "100%": { opacity: "0.8" },
        },
      },
    },
  },
  plugins: [],
};
