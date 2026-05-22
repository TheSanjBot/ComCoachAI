import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
        <input
          type={type}
          className={cn(
            "font-body flex h-12 w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.03)] outline-none transition-all duration-200 placeholder:text-white/30 focus-visible:border-primary focus-visible:bg-white/[0.05] focus-visible:ring-2 focus-visible:ring-primary/30 focus-visible:shadow-[0_12px_30px_-18px_rgba(247,147,26,0.65)] disabled:cursor-not-allowed disabled:opacity-50",
            className
          )}
          ref={ref}
          {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
