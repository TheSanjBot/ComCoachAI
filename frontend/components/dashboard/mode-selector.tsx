"use client";

import { motion } from "framer-motion";
import { BrainCircuit, FileSearch, Presentation } from "lucide-react";

import type { ModeDefinition, ModeId } from "@/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const icons = {
  interview: BrainCircuit,
  public_speaking: Presentation,
  resume_analysis: FileSearch
};

export function ModeSelector({
  modes,
  selectedMode,
  onSelect
}: {
  modes: ModeDefinition[];
  selectedMode: ModeId;
  onSelect: (mode: ModeId) => void;
}) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {modes.map((mode, index) => {
        const Icon = icons[mode.id];
        const selected = selectedMode === mode.id;
        return (
          <motion.button
            animate={{ y: 0, opacity: 1 }}
            className="text-left"
            initial={{ y: 12, opacity: 0 }}
            key={mode.id}
            onClick={() => onSelect(mode.id)}
            transition={{ delay: index * 0.08 }}
            type="button"
          >
            <Card
              className={cn(
                "h-full border-transparent transition-all hover:-translate-y-1",
                selected && "border-primary/40 ring-2 ring-primary/15"
              )}
            >
              <div className="mb-4 flex items-center justify-between">
                <span className="rounded-2xl bg-secondary p-3">
                  <Icon className="h-5 w-5 text-primary" />
                </span>
                {selected ? <Badge>Active Mode</Badge> : null}
              </div>
              <CardTitle>{mode.title}</CardTitle>
              <CardDescription className="mt-3 leading-6">
                {mode.description}
              </CardDescription>
            </Card>
          </motion.button>
        );
      })}
    </div>
  );
}

