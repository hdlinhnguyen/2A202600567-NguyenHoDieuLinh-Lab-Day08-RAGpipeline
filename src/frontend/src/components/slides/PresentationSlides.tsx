import { useCallback, useEffect, useState, type ElementType, type ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Database,
  Search,
  MessageSquare,
  Shield,
  Layers,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Mic,
  Upload,
  BookOpen,
} from "lucide-react";
import { BrandLogo } from "@/components/rag/BrandLogo";
import { fadeUp, staggerContainer, staggerItem } from "@/lib/motion";

type Slide = {
  id: string;
  tag: string;
  title: string;
  subtitle?: string;
  content: ReactNode;
};

const slideVariants = {
  enter: (dir: number) => ({
    x: dir > 0 ? 120 : -120,
    opacity: 0,
    scale: 0.94,
    filter: "blur(6px)",
  }),
  center: {
    x: 0,
    opacity: 1,
    scale: 1,
    filter: "blur(0px)",
  },
  exit: (dir: number) => ({
    x: dir > 0 ? -120 : 120,
    opacity: 0,
    scale: 0.94,
    filter: "blur(6px)",
  }),
};

function StatCard({ value, label, delay }: { value: string; label: string; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay, type: "spring", damping: 20, stiffness: 260 }}
      className="rounded-2xl border border-border bg-surface/80 backdrop-blur p-5 text-center shadow-soft"
    >
      <p className="text-3xl font-bold text-mint">{value}</p>
      <p className="text-sm text-muted-foreground mt-1">{label}</p>
    </motion.div>
  );
}

function PipelineStep({ icon: Icon, label, delay }: { icon: ElementType; label: string; delay: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -16 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay, type: "spring", stiffness: 280 }}
      className="flex items-center gap-3"
    >
      <div className="h-10 w-10 rounded-xl bg-mint-soft grid place-items-center shrink-0">
        <Icon className="h-5 w-5 text-mint" />
      </div>
      <span className="text-sm font-medium">{label}</span>
      <ArrowRight className="h-4 w-4 text-muted-foreground/50 hidden sm:block" />
    </motion.div>
  );
}

const SLIDES: Slide[] = [
  {
    id: "title",
    tag: "Day 8 · AI in Action",
    title: "",
    subtitle: "Chatbot Pháp luật Ma túy Việt Nam",
    content: (
      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="space-y-8">
        <motion.div variants={fadeUp} className="flex justify-center">
          <BrandLogo className="h-14 w-auto" />
        </motion.div>
        <motion.p variants={fadeUp} className="text-lg text-muted-foreground text-center max-w-xl mx-auto leading-relaxed">
          RAG pipeline end-to-end — từ văn bản pháp luật &amp; tin tức → indexing → hybrid retrieval → generation có citation
        </motion.p>
        <motion.div variants={staggerContainer} className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
          <StatCard value="10" label="Tasks" delay={0.2} />
          <StatCard value="2.139" label="Chunks" delay={0.3} />
          <StatCard value="35/35" label="Tests" delay={0.4} />
        </motion.div>
      </motion.div>
    ),
  },
  {
    id: "problem",
    tag: "Vấn đề",
    title: "Tại sao cần RAG?",
    subtitle: "Domain pháp luật — không được hallucinate",
    content: (
      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
        {[
          { icon: BookOpen, title: "Văn bản phức tạp", desc: "Bộ luật Hình sự, Luật 2021 — hàng nghìn điều khoản, khó tra cứu thủ công" },
          { icon: Shield, title: "Không bịa số liệu", desc: "Mức phạt tù phải có nguồn — LLM thuần dễ hallucinate Điều luật" },
          { icon: Search, title: "Đa nguồn dữ liệu", desc: "Kết hợp văn bản pháp luật + tin tức báo chí trong một điểm hỏi–đáp" },
          { icon: MessageSquare, title: "Có thể kiểm chứng", desc: "Mọi câu trả lời kèm citation — click xem excerpt nguồn gốc" },
        ].map((item, i) => (
          <motion.div
            key={item.title}
            variants={staggerItem}
            whileHover={{ y: -4, borderColor: "var(--mint)" }}
            className="rounded-2xl border border-border bg-surface/70 p-5 transition-colors"
          >
            <item.icon className="h-6 w-6 text-mint mb-3" />
            <h3 className="font-semibold mb-1">{item.title}</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
          </motion.div>
        ))}
      </motion.div>
    ),
  },
  {
    id: "pipeline",
    tag: "Kiến trúc",
    title: "RAG Pipeline",
    subtitle: "Task 1 → 10 · Modular & có fallback",
    content: (
      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="max-w-2xl mx-auto space-y-6">
        <motion.div variants={fadeUp} className="rounded-2xl border border-border bg-surface/60 p-6 space-y-3">
          <PipelineStep icon={Database} label="Thu thập PDF + Crawl tin tức" delay={0.1} />
          <PipelineStep icon={Layers} label="MarkItDown → Chunk 500 · Embed MiniLM" delay={0.15} />
          <PipelineStep icon={Search} label="Semantic + BM25 → RRF → Rerank" delay={0.2} />
          <PipelineStep icon={Sparkles} label="GPT-4o-mini + Guardrails + Citation" delay={0.25} />
        </motion.div>
        <motion.div variants={fadeUp} className="flex flex-wrap justify-center gap-2">
          {["Query Expansion", "Điều 249 Boost", "Lost-in-middle Reorder", "PageIndex Fallback"].map((tag, i) => (
            <motion.span
              key={tag}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.3 + i * 0.06 }}
              className="px-3 py-1.5 rounded-full text-xs font-medium bg-mint-soft text-mint border border-mint/20"
            >
              {tag}
            </motion.span>
          ))}
        </motion.div>
      </motion.div>
    ),
  },
  {
    id: "data",
    tag: "Dữ liệu",
    title: "Knowledge Base",
    subtitle: "4 văn bản pháp luật · 6 bài báo · Upload động",
    content: (
      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="max-w-3xl mx-auto">
        <motion.div variants={staggerContainer} className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <StatCard value="4" label="Legal PDF" delay={0.1} />
          <StatCard value="6" label="News articles" delay={0.15} />
          <StatCard value="1.741" label="Legal chunks" delay={0.2} />
          <StatCard value="397" label="News chunks" delay={0.25} />
        </motion.div>
        <motion.ul variants={staggerContainer} className="space-y-2">
          {[
            "Bộ luật Hình sự 2015 — Chương XX (ma túy)",
            "Luật Phòng chống ma túy 2021",
            "Thông tư danh mục chất ma túy",
            "6 bài báo nghệ sĩ — Tuổi Trẻ, VnExpress…",
          ].map((item) => (
            <motion.li
              key={item}
              variants={staggerItem}
              className="flex items-center gap-3 px-4 py-3 rounded-xl border border-border bg-surface/50 text-sm"
            >
              <CheckCircle2 className="h-4 w-4 text-mint shrink-0" />
              {item}
            </motion.li>
          ))}
        </motion.ul>
      </motion.div>
    ),
  },
  {
    id: "product",
    tag: "Sản phẩm",
    title: "Arionear Chatbot",
    subtitle: "React UI + FastAPI · Streamlit backup",
    content: (
      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid sm:grid-cols-2 gap-4 max-w-3xl mx-auto">
        {[
          { icon: MessageSquare, title: "Chat có citation", desc: "Sources Used — click xem excerpt" },
          { icon: Layers, title: "Follow-up memory", desc: "6 turn gần nhất — hiểu ngữ cảnh hội thoại" },
          { icon: Upload, title: "Upload Knowledge Base", desc: "PDF · DOCX · MD → auto re-index" },
          { icon: Mic, title: "Voice-to-text", desc: "Web Speech API tiếng Việt (vi-VN)" },
        ].map((item) => (
          <motion.div
            key={item.title}
            variants={staggerItem}
            whileHover={{ scale: 1.02 }}
            className="rounded-2xl border border-mint/20 bg-mint-soft/20 p-5"
          >
            <item.icon className="h-6 w-6 text-mint mb-2" />
            <h3 className="font-semibold text-sm">{item.title}</h3>
            <p className="text-xs text-muted-foreground mt-1">{item.desc}</p>
          </motion.div>
        ))}
        <motion.div variants={staggerItem} className="sm:col-span-2 rounded-2xl border border-border bg-surface/60 p-4 text-center">
          <p className="text-sm text-muted-foreground">
            Demo: <span className="text-foreground font-medium">"Hình phạt tàng trữ ma túy?"</span>
            {" → "}
            <span className="text-mint font-medium">Điều 249 · phạt tù 1–7 năm</span>
          </p>
        </motion.div>
      </motion.div>
    ),
  },
  {
    id: "demo",
    tag: "Demo",
    title: "Kịch bản trình bày",
    subtitle: "5 phút · Live demo",
    content: (
      <motion.ol variants={staggerContainer} initial="hidden" animate="show" className="max-w-2xl mx-auto space-y-3">
        {[
          "Hình phạt tội tàng trữ trái phép chất ma túy?",
          "Luật Phòng chống ma túy 2021 — cai nghiện?",
          "Nghệ sĩ nào bị bắt vì ma túy?",
          "Follow-up: Họ bị phạt bao nhiêu năm tù?",
          "Upload tài liệu mới + Voice-to-text",
        ].map((q, i) => (
          <motion.li
            key={q}
            variants={staggerItem}
            className="flex items-start gap-4 px-4 py-3 rounded-xl border border-border bg-surface/50"
          >
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.1 + i * 0.08, type: "spring" }}
              className="h-7 w-7 rounded-full bg-mint text-white text-sm font-bold grid place-items-center shrink-0"
            >
              {i + 1}
            </motion.span>
            <span className="text-sm pt-1">{q}</span>
          </motion.li>
        ))}
      </motion.ol>
    ),
  },
  {
    id: "closing",
    tag: "Kết luận",
    title: "Cảm ơn!",
    subtitle: "Q&A · Arionear RAG Pipeline",
    content: (
      <motion.div variants={staggerContainer} initial="hidden" animate="show" className="text-center space-y-6 max-w-xl mx-auto">
        <motion.div variants={fadeUp}>
          <BrandLogo className="h-12 w-auto mx-auto mb-4" />
        </motion.div>
        <motion.div variants={staggerContainer} className="space-y-2 text-sm text-muted-foreground">
          {[
            "35/35 automated tests passed",
            "Hybrid retrieval + Karpathy guardrails",
            "Next: RAGAS evaluation · bge-m3 embedding",
          ].map((line) => (
            <motion.p key={line} variants={staggerItem}>{line}</motion.p>
          ))}
        </motion.div>
        <motion.div variants={fadeUp}>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-mint text-white font-medium text-sm shadow-glow hover:opacity-90 transition-opacity"
          >
            Mở Chatbot
            <ArrowRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </motion.div>
    ),
  },
];

export function PresentationSlides() {
  const [index, setIndex] = useState(0);
  const [direction, setDirection] = useState(0);
  const total = SLIDES.length;
  const slide = SLIDES[index];

  const go = useCallback((next: number) => {
    if (next < 0 || next >= total) return;
    setDirection(next > index ? 1 : -1);
    setIndex(next);
  }, [index, total]);

  const prev = useCallback(() => go(index - 1), [go, index]);
  const next = useCallback(() => go(index + 1), [go, index]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); next(); }
      if (e.key === "ArrowLeft") { e.preventDefault(); prev(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, prev]);

  return (
    <div className="min-h-screen bg-background relative overflow-hidden flex flex-col">
      <motion.div
        className="pointer-events-none absolute -top-40 right-0 h-[500px] w-[500px] mint-glow opacity-40 animate-float-slow"
        animate={{ opacity: [0.3, 0.5, 0.3] }}
        transition={{ repeat: Infinity, duration: 8 }}
      />
      <motion.div
        className="pointer-events-none absolute -bottom-32 left-0 h-[400px] w-[400px] mint-glow opacity-30 animate-float-slower"
      />

      {/* Progress bar */}
      <div className="relative h-1 bg-border/50">
        <motion.div
          className="h-full bg-mint"
          initial={false}
          animate={{ width: `${((index + 1) / total) * 100}%` }}
          transition={{ type: "spring", damping: 24, stiffness: 200 }}
        />
      </div>

      {/* Header */}
      <header className="relative flex items-center justify-between px-6 py-4">
        <span className="text-xs uppercase tracking-widest text-muted-foreground">{slide.tag}</span>
        <span className="text-xs font-mono text-muted-foreground">
          {index + 1} / {total}
        </span>
      </header>

      {/* Slide content */}
      <main className="relative flex-1 flex items-center justify-center px-8 md:px-16 py-6 overflow-hidden">
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={slide.id}
            custom={direction}
            variants={slideVariants}
            initial="enter"
            animate="center"
            exit="exit"
            transition={{ type: "spring", damping: 26, stiffness: 220 }}
            className="w-full max-w-4xl"
          >
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 }}
              className="text-3xl md:text-5xl font-bold tracking-tight text-center mb-2"
            >
              {slide.title}
            </motion.h1>
            {slide.subtitle && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.12 }}
                className="text-center text-muted-foreground mb-10 text-sm md:text-base"
              >
                {slide.subtitle}
              </motion.p>
            )}
            {slide.content}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Navigation */}
      <footer className="relative px-6 pb-8 pt-4">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <motion.button
            onClick={prev}
            disabled={index === 0}
            whileHover={index > 0 ? { x: -4, scale: 1.05 } : {}}
            whileTap={index > 0 ? { scale: 0.95 } : {}}
            className="flex items-center gap-2 px-5 py-3 rounded-2xl border border-border bg-surface/80 backdrop-blur text-sm font-medium disabled:opacity-30 disabled:cursor-not-allowed hover:border-mint/50 transition-colors shadow-soft"
          >
            <ChevronLeft className="h-5 w-5" />
            Trước
          </motion.button>

          <div className="flex items-center gap-2">
            {SLIDES.map((s, i) => (
              <motion.button
                key={s.id}
                onClick={() => go(i)}
                whileHover={{ scale: 1.2 }}
                className="p-1"
                aria-label={`Slide ${i + 1}`}
              >
                <motion.span
                  animate={{
                    width: i === index ? 24 : 8,
                    backgroundColor: i === index ? "var(--mint)" : "var(--border)",
                  }}
                  className="block h-2 rounded-full"
                  transition={{ type: "spring", stiffness: 300, damping: 22 }}
                />
              </motion.button>
            ))}
          </div>

          <motion.button
            onClick={next}
            disabled={index === total - 1}
            whileHover={index < total - 1 ? { x: 4, scale: 1.05 } : {}}
            whileTap={index < total - 1 ? { scale: 0.95 } : {}}
            className="flex items-center gap-2 px-5 py-3 rounded-2xl border border-border bg-surface/80 backdrop-blur text-sm font-medium disabled:opacity-30 disabled:cursor-not-allowed hover:border-mint/50 transition-colors shadow-soft"
          >
            Tiếp
            <ChevronRight className="h-5 w-5" />
          </motion.button>
        </div>
      </footer>
    </div>
  );
}
