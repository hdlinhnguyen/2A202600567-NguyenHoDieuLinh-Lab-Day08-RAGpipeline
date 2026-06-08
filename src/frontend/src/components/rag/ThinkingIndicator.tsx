import { motion, AnimatePresence } from "framer-motion";
import { Brain, Database, Search, Sparkles, GitMerge } from "lucide-react";
import { scaleIn } from "@/lib/motion";

const STEP_ICONS = [Brain, Search, Database, GitMerge, Sparkles];

export function ThinkingIndicator({ status }: { status: string }) {
  const Icon = STEP_ICONS[status.length % STEP_ICONS.length];

  return (
    <motion.div
      variants={scaleIn}
      initial="hidden"
      animate="show"
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.15 } }}
      className="flex items-start gap-3 rounded-2xl border border-mint/20 bg-mint-soft/30 px-4 py-3 overflow-hidden relative"
    >
      <div className="absolute inset-0 animate-shimmer opacity-40 pointer-events-none" />
      <motion.div
        animate={{ rotate: [0, 8, -8, 0] }}
        transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
        className="relative h-8 w-8 shrink-0 rounded-xl bg-mint/20 grid place-items-center"
      >
        <Icon className="h-4 w-4 text-mint" />
      </motion.div>
      <div className="relative space-y-1.5 min-w-0">
        <AnimatePresence mode="wait">
          <motion.p
            key={status}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2 }}
            className="text-sm text-foreground/80"
          >
            {status}
          </motion.p>
        </AnimatePresence>
        <div className="flex items-center gap-1">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-1.5 w-1.5 rounded-full bg-mint"
              animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.1, 0.8] }}
              transition={{ repeat: Infinity, duration: 1.2, delay: i * 0.2 }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}
