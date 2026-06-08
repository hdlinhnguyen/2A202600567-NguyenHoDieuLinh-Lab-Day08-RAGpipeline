import { motion } from "framer-motion";
import logoUrl from "../../../assets/image.png";
import { scaleIn } from "@/lib/motion";

export function BrandLogo({ className = "h-8 w-auto" }: { className?: string }) {
  return (
    <motion.img
      src={logoUrl}
      alt="Arionear"
      className={`object-contain ${className}`}
      variants={scaleIn}
      initial="hidden"
      animate="show"
      whileHover={{ scale: 1.03 }}
      transition={{ type: "spring", damping: 20, stiffness: 300 }}
    />
  );
}
