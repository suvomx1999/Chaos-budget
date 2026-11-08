interface LoaderProps {
  message?: string;
  size?: "sm" | "md" | "lg";
}

export default function Loader({
  message = "Loading...",
  size = "md",
}: LoaderProps) {
  const ring = { sm: "h-5 w-5", md: "h-8 w-8", lg: "h-12 w-12" };
  const text = { sm: "text-xs", md: "text-sm", lg: "text-base" };

  return (
    <div className="flex flex-col items-center justify-center gap-4 py-12">
      <div
        className={`${ring[size]} rounded-full border-2 border-primary/20 border-t-primary animate-spin`}
      />
      <p className={`${text[size]} text-text-muted animate-pulse`}>
        {message}
      </p>
    </div>
  );
}
