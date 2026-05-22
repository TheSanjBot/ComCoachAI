import { cn } from "@/lib/utils";

export function Progress({
  value,
  className
}: {
  value: number;
  className?: string;
}) {
  return (
    <div className={cn("h-2.5 w-full rounded-full border border-white/10 bg-white/[0.05]", className)}>
      <div
        className="h-full rounded-full bg-gradient-to-r from-burnt to-primary shadow-orange-glow transition-all"
        style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </div>
  );
}
