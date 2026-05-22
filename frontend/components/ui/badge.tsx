import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "font-mono inline-flex items-center rounded-full border border-primary/30 bg-primary/12 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.22em] text-primary shadow-orange-glow",
        className
      )}
      {...props}
    />
  );
}
