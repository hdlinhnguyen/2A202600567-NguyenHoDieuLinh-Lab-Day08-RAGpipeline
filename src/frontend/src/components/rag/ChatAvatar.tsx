import { motion } from "framer-motion";
import avatarUrl from "../../../assets/logo.png";
import { scaleIn } from "@/lib/motion";

export function ChatAvatar({ className = "h-9 w-9 rounded-2xl" }: { className?: string }) {
  return (
    <motion.div
      variants={scaleIn}
      initial="hidden"
      animate="show"
      className={`shrink-0 bg-white border border-border grid place-items-center overflow-hidden shadow-soft ${className}`}
    >
      <motion.img
        src={avatarUrl}
        alt="Arionear"
        className="h-[70%] w-[70%] object-contain"
        animate={{ scale: [1, 1.04, 1] }}
        transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
      />
    </motion.div>
  );
}
