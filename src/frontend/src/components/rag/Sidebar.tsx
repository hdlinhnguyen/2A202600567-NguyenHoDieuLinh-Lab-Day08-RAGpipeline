import { motion, AnimatePresence, LayoutGroup } from "framer-motion";
import { Plus, Settings, ChevronDown, MessageSquare } from "lucide-react";
import { BrandLogo } from "@/components/rag/BrandLogo";
import { ChatAvatar } from "@/components/rag/ChatAvatar";
import type { ChatSession } from "@/lib/rag-types";
import { fadeUp, hoverLift, slideLeft, staggerContainer, staggerItem } from "@/lib/motion";

type RagSidebarProps = {
  onNewChat: () => void;
  sessions: ChatSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
};

export function RagSidebar({
  onNewChat,
  sessions,
  activeSessionId,
  onSelectSession,
}: RagSidebarProps) {
  return (
    <motion.aside
      variants={slideLeft}
      initial="hidden"
      animate="show"
      className="hidden md:flex w-[280px] shrink-0 flex-col rounded-3xl border border-border bg-surface/60 backdrop-blur-xl shadow-soft overflow-hidden relative"
    >
      <motion.div
        className="pointer-events-none absolute -bottom-20 -left-10 h-72 w-72 mint-glow opacity-80 animate-pulse-glow"
        animate={{ opacity: [0.5, 0.85, 0.5] }}
        transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
      />

      <motion.div variants={fadeUp} className="relative px-4 pt-5 pb-3">
        <BrandLogo className="h-8 w-auto max-w-[160px] mb-4" />
        <motion.button
          onClick={onNewChat}
          {...hoverLift}
          className="group w-full flex items-center justify-center gap-2 rounded-xl bg-surface border border-border py-3 text-sm font-medium hover:border-mint/50 hover:shadow-glow transition-colors"
        >
          <motion.span
            animate={{ rotate: [0, 90, 0] }}
            transition={{ repeat: Infinity, duration: 8, ease: "easeInOut" }}
          >
            <Plus className="h-4 w-4" />
          </motion.span>
          Cuộc chat mới
        </motion.button>
      </motion.div>

      <div className="relative flex-1 overflow-y-auto scrollbar-thin px-4 py-3">
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-[11px] uppercase tracking-wider text-muted-foreground mb-2 px-2"
        >
          Lịch sử chat
        </motion.p>

        <AnimatePresence mode="popLayout">
          {sessions.length === 0 ? (
            <motion.p
              key="empty"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="px-3 py-4 text-sm text-muted-foreground"
            >
              Chưa có cuộc trò chuyện nào.
            </motion.p>
          ) : (
            <motion.ul
              key="list"
              variants={staggerContainer}
              initial="hidden"
              animate="show"
              className="space-y-1"
            >
              <LayoutGroup>
                {sessions.map((session) => (
                  <motion.li
                    key={session.id}
                    layout
                    variants={staggerItem}
                    exit="exit"
                  >
                    <motion.button
                      layout
                      onClick={() => onSelectSession(session.id)}
                      whileHover={{ x: 3 }}
                      whileTap={{ scale: 0.98 }}
                      className={`relative w-full flex items-start gap-2 text-left px-3 py-2.5 text-sm rounded-lg transition-colors ${
                        activeSessionId === session.id
                          ? "text-foreground"
                          : "text-foreground/75 hover:bg-muted"
                      }`}
                    >
                      {activeSessionId === session.id && (
                        <motion.span
                          layoutId="active-session"
                          className="absolute inset-0 rounded-lg bg-mint-soft border border-mint/30"
                          transition={{ type: "spring", damping: 24, stiffness: 300 }}
                        />
                      )}
                      <MessageSquare className="relative h-4 w-4 shrink-0 mt-0.5 text-mint" />
                      <span className="relative truncate">{session.title}</span>
                    </motion.button>
                  </motion.li>
                ))}
              </LayoutGroup>
            </motion.ul>
          )}
        </AnimatePresence>
      </div>

      <motion.div
        variants={fadeUp}
        initial="hidden"
        animate="show"
        transition={{ delay: 0.3 }}
        className="relative p-3 border-t border-border/60"
      >
        <motion.button
          {...hoverLift}
          className="w-full flex items-center gap-3 p-2 rounded-xl bg-surface border border-border"
        >
          <ChatAvatar className="h-9 w-9 rounded-full" />
          <div className="flex-1 text-left min-w-0">
            <p className="text-sm font-medium leading-tight truncate">Người dùng</p>
            <p className="text-[11px] text-muted-foreground leading-tight truncate">Arionear RAG</p>
          </div>
          <motion.span whileHover={{ rotate: 45 }} transition={{ type: "spring", stiffness: 300 }}>
            <Settings className="h-4 w-4 text-muted-foreground shrink-0" />
          </motion.span>
          <motion.span animate={{ y: [0, 2, 0] }} transition={{ repeat: Infinity, duration: 2 }}>
            <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
          </motion.span>
        </motion.button>
      </motion.div>
    </motion.aside>
  );
}
