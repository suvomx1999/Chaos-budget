import { type ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
}

export default function Card({
  children,
  className = "",
  hover = false,
  glow = false,
}: CardProps) {
  return (
    <div
      className={`
        bg-bg-card/60 backdrop-blur-sm border border-white/[0.06] rounded-2xl p-6
        ${hover ? "hover:bg-bg-card-hover hover:border-white/[0.10] transition-all duration-300 cursor-pointer" : ""}
        ${glow ? "card-glow" : ""}
        ${className}
      `}
    >
      {children}
    </div>
  );
}
