import { motion } from "framer-motion";
import { PanelRight } from "lucide-react";
import { fadeUp, iconTap } from "@/lib/motion";

export function TopBar({ onToggleRight }: { onToggleRight: () => void }) {
  return (
    <motion.header
      variants={fadeUp}
      initial="hidden"
      animate="show"
      className="flex items-center justify-end px-2 mb-4"
    >
      <motion.button
        onClick={onToggleRight}
        {...iconTap}
        className="h-10 w-10 grid place-items-center rounded-full glass border border-border hover:border-mint/50 transition-colors"
        aria-label="Mở/đóng Knowledge Base"
      >
        <PanelRight className="h-4 w-4" />
      </motion.button>
    </motion.header>
  );
}
