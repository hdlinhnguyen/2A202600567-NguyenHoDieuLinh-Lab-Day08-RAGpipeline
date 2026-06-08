import type { Transition, Variants } from "framer-motion";

export const spring: Transition = { type: "spring", damping: 22, stiffness: 280 };
export const springSoft: Transition = { type: "spring", damping: 28, stiffness: 200 };
export const springBouncy: Transition = { type: "spring", damping: 18, stiffness: 320 };

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: springSoft },
  exit: { opacity: 0, y: -10, transition: { duration: 0.18 } },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
};

export const slideLeft: Variants = {
  hidden: { opacity: 0, x: -28 },
  show: { opacity: 1, x: 0, transition: spring },
  exit: { opacity: 0, x: -16, transition: { duration: 0.2 } },
};

export const slideRight: Variants = {
  hidden: { opacity: 0, x: 32 },
  show: { opacity: 1, x: 0, transition: spring },
  exit: { opacity: 0, x: 20, transition: { duration: 0.2 } },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.9 },
  show: { opacity: 1, scale: 1, transition: spring },
  exit: { opacity: 0, scale: 0.95, transition: { duration: 0.15 } },
};

export const pageShell: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { duration: 0.45, staggerChildren: 0.07, delayChildren: 0.05 },
  },
};

export const staggerContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06, delayChildren: 0.04 } },
};

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: springSoft },
  exit: { opacity: 0, x: -10, transition: { duration: 0.15 } },
};

export const messageUser: Variants = {
  hidden: { opacity: 0, x: 24, scale: 0.96 },
  show: { opacity: 1, x: 0, scale: 1, transition: springSoft },
};

export const messageAssistant: Variants = {
  hidden: { opacity: 0, x: -16, y: 8 },
  show: { opacity: 1, x: 0, y: 0, transition: springSoft },
};

export const hoverLift = {
  whileHover: { y: -2, transition: springSoft },
  whileTap: { scale: 0.97, transition: { duration: 0.1 } },
};

export const iconTap = {
  whileHover: { scale: 1.08, transition: springSoft },
  whileTap: { scale: 0.92 },
};
