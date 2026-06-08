import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, ExternalLink, FileText, RotateCw, ThumbsUp } from "lucide-react";
import type { Message, Source } from "@/lib/rag-types";
import { ChatAvatar } from "@/components/rag/ChatAvatar";
import { ThinkingIndicator } from "@/components/rag/ThinkingIndicator";
import { iconTap, messageAssistant, messageUser, staggerContainer, staggerItem } from "@/lib/motion";

export function ChatFeed({
  messages, onOpenSource, streaming,
}: { messages: Message[]; onOpenSource: (s: Source) => void; streaming: boolean }) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-8 pb-6"
    >
      <AnimatePresence initial={false} mode="popLayout">
        {messages.map((m) => (
          <motion.div
            key={m.id}
            layout
            variants={m.role === "user" ? messageUser : messageAssistant}
            initial="hidden"
            animate="show"
            exit={{ opacity: 0, scale: 0.96, transition: { duration: 0.15 } }}
            className={m.role === "user" ? "flex justify-end" : "flex gap-3"}
          >
            {m.role === "assistant" && <ChatAvatar />}
            <div className={m.role === "user"
              ? "max-w-[80%] rounded-2xl rounded-tr-md bg-foreground text-background px-4 py-3 text-[15px] leading-relaxed shadow-soft"
              : "max-w-[78%] space-y-3"
            }>
              {m.role === "assistant" ? (
                <>
                  <AnimatePresence mode="wait">
                    {m.status && !m.content ? (
                      <ThinkingIndicator key={m.status} status={m.status} />
                    ) : null}
                  </AnimatePresence>
                  {m.content ? (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.25 }}
                      className="prose prose-sm max-w-none text-foreground/90 prose-headings:font-semibold prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-[12.5px] prose-pre:bg-surface-2 prose-pre:border prose-pre:border-border"
                    >
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
                    </motion.div>
                  ) : null}
                  <AnimatePresence>
                    {m.content && streaming === false && (
                      <motion.div
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        transition={{ delay: 0.15 }}
                        className="flex items-center gap-1 -ml-1"
                      >
                        <IconBtn><Copy className="h-3.5 w-3.5" /></IconBtn>
                        <IconBtn><RotateCw className="h-3.5 w-3.5" /></IconBtn>
                        <IconBtn><ThumbsUp className="h-3.5 w-3.5" /></IconBtn>
                      </motion.div>
                    )}
                  </AnimatePresence>
                  {m.sources?.length ? (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2 }}
                      className="pt-1"
                    >
                      <p className="text-[11px] uppercase tracking-wider text-muted-foreground mb-2">Sources Used</p>
                      <motion.div
                        variants={staggerContainer}
                        initial="hidden"
                        animate="show"
                        className="flex flex-wrap gap-2"
                      >
                        {m.sources.map((s, i) => (
                          <motion.div
                            key={i}
                            variants={staggerItem}
                            className="group flex items-center gap-1 max-w-[300px]"
                          >
                            <motion.button
                              whileHover={{ y: -2, scale: 1.02 }}
                              whileTap={{ scale: 0.97 }}
                              onClick={() => onOpenSource(s)}
                              className="flex flex-1 items-center gap-2 min-w-0 px-3 py-2 rounded-xl border border-border bg-surface hover:border-mint/50 hover:shadow-glow transition-colors text-left"
                            >
                              <motion.span
                                whileHover={{ rotate: [0, -8, 8, 0] }}
                                transition={{ duration: 0.4 }}
                                className="h-6 w-6 grid place-items-center rounded-md bg-mint-soft text-primary text-[10px] font-mono font-semibold shrink-0"
                              >
                                {i + 1}
                              </motion.span>
                              <span className="flex flex-col min-w-0 flex-1">
                                <span className="text-xs font-medium truncate">{s.title}</span>
                                <span className="text-[10px] text-muted-foreground truncate">{s.snippet}</span>
                                {s.url && (
                                  <span className="text-[10px] text-mint truncate mt-0.5">{s.url}</span>
                                )}
                              </span>
                              <FileText className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                            </motion.button>
                            {s.url && (
                              <motion.a
                                href={s.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                whileHover={{ scale: 1.08 }}
                                whileTap={{ scale: 0.92 }}
                                onClick={(e) => e.stopPropagation()}
                                className="h-8 w-8 grid place-items-center rounded-lg border border-border bg-surface hover:border-mint/50 text-mint shrink-0"
                                aria-label="Mở link nguồn"
                              >
                                <ExternalLink className="h-3.5 w-3.5" />
                              </motion.a>
                            )}
                          </motion.div>
                        ))}
                      </motion.div>
                    </motion.div>
                  ) : null}
                </>
              ) : (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  {m.content}
                </motion.p>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
}

function IconBtn({ children }: { children: React.ReactNode }) {
  return (
    <motion.button
      {...iconTap}
      className="h-7 w-7 grid place-items-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
    >
      {children}
    </motion.button>
  );
}
