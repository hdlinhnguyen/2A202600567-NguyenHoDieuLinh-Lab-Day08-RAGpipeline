import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, BookOpen, FileSearch, Calculator, GitBranch, Search } from "lucide-react";
import { fadeUp, pageShell, scaleIn, staggerContainer, staggerItem } from "@/lib/motion";

import { RagSidebar } from "@/components/rag/Sidebar";
import { TopBar } from "@/components/rag/TopBar";
import { Composer } from "@/components/rag/Composer";
import { ChatFeed } from "@/components/rag/ChatFeed";
import { KnowledgePanel } from "@/components/rag/KnowledgePanel";
import { SourceDialog } from "@/components/rag/SourceDialog";
import type { ChatSession, Message, Source } from "@/lib/rag-types";
import { sendChatMessage } from "@/lib/api/rag";
import {
  buildSessionTitle,
  loadChatSessions,
  upsertChatSession,
} from "@/lib/chat-history";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Arionear · RAG Pháp luật Ma túy" },
      { name: "description", content: "A premium RAG chatbot workspace — query your documents with cited, streaming AI responses." },
    ],
  }),
  component: Index,
});

const THINKING_STEPS = [
  "Đang phân tích câu hỏi...",
  "Đang tra cứu knowledge base...",
  "Đang tìm kiếm semantic + BM25...",
  "Đang rerank và chọn nguồn liên quan...",
  "Đang suy luận và tổng hợp câu trả lời...",
];

const suggestions = [
  { icon: BookOpen, label: "Hình phạt tàng trữ ma túy" },
  { icon: FileSearch, label: "Luật phòng chống ma túy 2021" },
  { icon: Calculator, label: "Nghệ sĩ bị bắt vì ma túy" },
  { icon: GitBranch, label: "Quy định cai nghiện" },
  { icon: Search, label: "Danh mục chất ma túy" },
];

function Index() {
  const [sessions, setSessions] = useState<ChatSession[]>(() => loadChatSessions());
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [openSource, setOpenSource] = useState<Source | null>(null);
  const [rightOpen, setRightOpen] = useState(true);
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, streaming]);

  const persistSession = (sessionId: string, msgs: Message[]) => {
    if (msgs.length === 0) return;
    const session: ChatSession = {
      id: sessionId,
      title: buildSessionTitle(msgs),
      messages: msgs,
      updatedAt: Date.now(),
    };
    setSessions((prev) => upsertChatSession(prev, session));
  };

  const handleNewChat = () => {
    if (activeSessionId && messages.length > 0) {
      persistSession(activeSessionId, messages);
    }
    setActiveSessionId(null);
    setMessages([]);
  };

  const handleSelectSession = (id: string) => {
    if (activeSessionId && messages.length > 0) {
      persistSession(activeSessionId, messages);
    }
    const session = sessions.find((s) => s.id === id);
    if (!session) return;
    setActiveSessionId(id);
    setMessages(session.messages);
  };

  const handleSend = async (text: string) => {
    const sessionId = activeSessionId ?? crypto.randomUUID();
    if (!activeSessionId) setActiveSessionId(sessionId);

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: text };
    const assistantId = crypto.randomUUID();
    setMessages((m) => [
      ...m,
      userMsg,
      { id: assistantId, role: "assistant", content: "", status: THINKING_STEPS[0] },
    ]);
    setStreaming(true);

    let step = 0;
    const thinkingTimer = setInterval(() => {
      step = (step + 1) % THINKING_STEPS.length;
      setMessages((m) =>
        m.map((msg) =>
          msg.id === assistantId && !msg.content
            ? { ...msg, status: THINKING_STEPS[step] }
            : msg,
        ),
      );
    }, 2800);

    try {
      const history = messages;
      const result = await sendChatMessage(text, history);
      clearInterval(thinkingTimer);
      const words = result.answer.split(" ");
      for (let i = 0; i < words.length; i++) {
        await new Promise((r) => setTimeout(r, 12));
        setMessages((m) =>
          m.map((msg) =>
            msg.id === assistantId
              ? { ...msg, content: words.slice(0, i + 1).join(" "), status: undefined }
              : msg,
          ),
        );
      }
      setMessages((m) => {
        const updated = m.map((msg) =>
          msg.id === assistantId ? { ...msg, sources: result.sources } : msg,
        );
        persistSession(sessionId, updated);
        return updated;
      });
    } catch (err) {
      clearInterval(thinkingTimer);
      const message = err instanceof Error ? err.message : "Lỗi không xác định";
      setMessages((m) => {
        const updated = m.map((msg) =>
          msg.id === assistantId
            ? {
                ...msg,
                content: `❌ Không thể kết nối RAG API. Hãy chạy backend:\n\n\`uvicorn group_project.chatbot.api:app --reload --port 8000\`\n\nChi tiết: ${message}`,
                status: undefined,
              }
            : msg,
        );
        persistSession(sessionId, updated);
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  };

  const empty = messages.length === 0;

  return (
    <div className="min-h-screen p-3 md:p-5 bg-background relative overflow-hidden">
      <motion.div
        className="pointer-events-none absolute -top-32 right-1/4 h-[420px] w-[420px] mint-glow opacity-50 animate-float-slow"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 0.5, scale: 1 }}
        transition={{ duration: 1.2 }}
      />
      <motion.div
        className="pointer-events-none absolute -bottom-40 left-1/3 h-[360px] w-[360px] mint-glow opacity-35 animate-float-slower"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.35 }}
        transition={{ duration: 1.5, delay: 0.3 }}
      />

      <motion.div
        variants={pageShell}
        initial="hidden"
        animate="show"
        className="relative flex gap-4 h-[calc(100vh-24px)] md:h-[calc(100vh-40px)]"
      >
        <RagSidebar
          onNewChat={handleNewChat}
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
        />

        <motion.main
          variants={scaleIn}
          className="flex-1 flex flex-col min-w-0 rounded-3xl border border-border bg-surface/40 backdrop-blur-xl shadow-soft p-4 md:p-5 overflow-hidden relative"
        >
          <motion.div
            className="pointer-events-none absolute top-0 right-0 h-48 w-48 mint-glow opacity-40 animate-pulse-glow"
          />
          <TopBar onToggleRight={() => setRightOpen((v) => !v)} />

          <AnimatePresence mode="wait">
            {empty ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, y: -20, transition: { duration: 0.25 } }}
                className="flex-1 flex flex-col"
              >
                <EmptyState onPick={handleSend} />
              </motion.div>
            ) : (
              <motion.div
                key="feed"
                ref={feedRef}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, transition: { duration: 0.2 } }}
                transition={{ type: "spring", damping: 24, stiffness: 220 }}
                className="flex-1 overflow-y-auto scrollbar-thin px-1 md:px-6 max-w-4xl w-full mx-auto"
              >
                <ChatFeed messages={messages} streaming={streaming} onOpenSource={setOpenSource} />
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div
            layout
            className="mt-4 max-w-3xl w-full mx-auto px-1"
          >
            <Composer onSend={handleSend} compact={!empty} isLoading={streaming} />
          </motion.div>
        </motion.main>

        <KnowledgePanel open={rightOpen} onClose={() => setRightOpen(false)} />
      </motion.div>

      <SourceDialog source={openSource} onClose={() => setOpenSource(null)} />
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="flex-1 flex flex-col items-center justify-center px-4 max-w-3xl w-full mx-auto"
    >
      <motion.h2
        variants={fadeUp}
        className="text-2xl md:text-[32px] font-semibold tracking-tight text-center leading-tight"
      >
        Chatbot{" "}
        <motion.span
          className="text-mint inline-block"
          animate={{ y: [0, -3, 0] }}
          transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
        >
          Pháp luật Ma túy
        </motion.span>
      </motion.h2>
      <motion.p
        variants={fadeUp}
        className="mt-2 text-sm text-muted-foreground text-center max-w-md"
      >
        Hỏi về luật pháp, hình phạt, cai nghiện hoặc tin tức — mọi câu trả lời đều kèm citation từ nguồn đã index.
      </motion.p>

      <motion.div
        variants={staggerContainer}
        className="mt-7 flex flex-wrap justify-center gap-2"
      >
        {suggestions.map((s) => (
          <motion.button
            key={s.label}
            variants={staggerItem}
            whileHover={{ y: -4, scale: 1.03 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => onPick(s.label + " theo pháp luật Việt Nam?")}
            className="flex items-center gap-2 px-4 py-2 rounded-full glass border border-border text-sm hover:border-mint/50 hover:shadow-glow transition-colors"
          >
            <motion.span
              whileHover={{ rotate: [0, -10, 10, 0] }}
              transition={{ duration: 0.4 }}
            >
              <s.icon className="h-3.5 w-3.5 text-mint" />
            </motion.span>
            {s.label}
          </motion.button>
        ))}
        <motion.button
          variants={staggerItem}
          whileHover={{ y: -4, scale: 1.03 }}
          whileTap={{ scale: 0.96 }}
          className="flex items-center gap-2 px-4 py-2 rounded-full glass border border-border text-sm hover:border-mint/50 transition-colors"
        >
          <motion.span
            animate={{ rotate: [0, 15, -15, 0] }}
            transition={{ repeat: Infinity, duration: 4 }}
          >
            <Sparkles className="h-3.5 w-3.5 text-mint" />
          </motion.span>
          Auto-suggest
        </motion.button>
      </motion.div>
    </motion.div>
  );
}
