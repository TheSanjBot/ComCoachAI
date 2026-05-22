import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "font-body inline-flex min-h-11 items-center justify-center rounded-full border text-sm font-semibold uppercase tracking-[0.22em] transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "border-primary/80 bg-gradient-to-r from-burnt to-primary text-primary-foreground shadow-orange-glow hover:scale-[1.02] hover:shadow-orange-glow-strong",
        secondary:
          "border-white/10 bg-surface/90 text-secondary-foreground shadow-panel-glow hover:-translate-y-0.5 hover:border-primary/50 hover:bg-surface/95",
        outline:
          "border-white/20 bg-white/[0.03] text-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] hover:border-white/60 hover:bg-white/[0.08]",
        ghost: "border-transparent text-muted-foreground hover:bg-white/[0.05] hover:text-primary",
        link: "border-transparent px-0 text-primary shadow-none hover:text-gold hover:underline"
      },
      size: {
        default: "px-5 py-2.5",
        sm: "min-h-10 px-4 text-xs tracking-[0.18em]",
        lg: "min-h-12 px-6 text-base tracking-[0.2em]"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  )
);

Button.displayName = "Button";

export { Button, buttonVariants };
