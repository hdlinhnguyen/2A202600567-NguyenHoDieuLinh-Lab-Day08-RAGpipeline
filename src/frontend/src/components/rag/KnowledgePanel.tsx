import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, FileText, CheckCircle2, Upload, Loader2 } from "lucide-react";
import { fetchKnowledgeBase, uploadDocument, type KnowledgeBaseInfo } from "@/lib/api/rag";
import { fadeUp, slideRight, staggerContainer, staggerItem } from "@/lib/motion";

const ACCEPT = ".pdf,.docx,.doc,.md,.txt";

export function KnowledgePanel({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [kb, setKb] = useState<KnowledgeBaseInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const loadKb = useCallback(() => {
    fetchKnowledgeBase()
      .then(setKb)
      .catch((e) => setError(e instanceof Error ? e.message : "Lỗi tải dữ liệu"));
  }, []);

  useEffect(() => {
    if (!open) return;
    loadKb();
  }, [open, loadKb]);

  const handleFiles = async (files: FileList | File[]) => {
    const file = files[0];
    if (!file) return;

    setUploading(true);
    setUploadMsg(null);
    setError(null);

    try {
      const result = await uploadDocument(file);
      if (result.success) {
        setUploadMsg(`✓ Đã thêm "${result.filename}" — ${result.total_chunks} chunks`);
        if (result.knowledge_base) setKb(result.knowledge_base);
        else loadKb();
      } else {
        setError(result.error ?? "Upload thất bại");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload lỗi");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (!uploading) void handleFiles(e.dataTransfer.files);
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          variants={slideRight}
          initial="hidden"
          animate="show"
          exit="exit"
          className="hidden xl:flex w-[340px] shrink-0 flex-col rounded-3xl border border-border bg-surface/70 backdrop-blur-xl shadow-soft overflow-hidden relative"
        >
          <motion.div
            className="pointer-events-none absolute -top-16 -right-10 h-56 w-56 mint-glow opacity-60 animate-float-slow"
          />

          <motion.div variants={fadeUp} className="relative flex items-center justify-between p-4 border-b border-border/60">
            <div>
              <h2 className="text-sm font-semibold">Knowledge Base</h2>
              <p className="text-[11px] text-muted-foreground">
                {kb ? `${kb.total_documents} tài liệu · ${kb.total_chunks} chunks` : "Đang tải..."}
              </p>
            </div>
            <motion.button
              onClick={onClose}
              whileHover={{ rotate: 90, scale: 1.05 }}
              whileTap={{ scale: 0.9 }}
              transition={{ type: "spring", stiffness: 300 }}
              className="h-8 w-8 grid place-items-center rounded-lg hover:bg-muted"
            >
              <X className="h-4 w-4" />
            </motion.button>
          </motion.div>

          <div className="relative p-4">
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPT}
              className="hidden"
              onChange={(e) => e.target.files && void handleFiles(e.target.files)}
            />
            <motion.button
              type="button"
              disabled={uploading}
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              animate={{
                scale: dragOver ? 1.02 : 1,
                borderColor: dragOver ? "var(--mint)" : undefined,
              }}
              whileHover={!uploading ? { y: -2 } : {}}
              whileTap={!uploading ? { scale: 0.98 } : {}}
              className={`w-full flex flex-col items-center justify-center gap-2 py-6 rounded-2xl border border-dashed transition-colors ${
                dragOver
                  ? "border-mint bg-mint-soft/30"
                  : "border-border bg-surface-2/50 hover:border-mint/50 hover:bg-mint-soft/20"
              } ${uploading ? "opacity-60 cursor-wait" : "cursor-pointer"}`}
            >
              {uploading ? (
                <Loader2 className="h-5 w-5 text-mint animate-spin" />
              ) : (
                <motion.span
                  animate={{ y: [0, -4, 0] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                >
                  <Upload className="h-5 w-5 text-mint" />
                </motion.span>
              )}
              <span className="text-sm font-medium">
                {uploading ? "Đang xử lý & index..." : "Upload tài liệu"}
              </span>
              <span className="text-[11px] text-muted-foreground">PDF · DOCX · MD · TXT (max 20MB)</span>
            </motion.button>

            <AnimatePresence>
              {uploadMsg && (
                <motion.p
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-[11px] text-mint mt-2"
                >
                  {uploadMsg}
                </motion.p>
              )}
              {error && (
                <motion.p
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-[11px] text-red-500 mt-2"
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>
          </div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="px-4 pb-2 text-[11px] text-muted-foreground"
          >
            {kb && (
              <p>
                📜 Legal: {kb.legal_count} · 📰 News: {kb.news_count}
                {(kb.upload_count ?? 0) > 0 ? ` · 📤 Upload: ${kb.upload_count}` : ""}
              </p>
            )}
          </motion.div>

          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="show"
            className="relative flex-1 overflow-y-auto px-4 scrollbar-thin space-y-2 pb-4"
          >
            {kb?.documents.map((f) => (
              <motion.div
                key={f.name}
                variants={staggerItem}
                whileHover={{ x: 4, borderColor: "color-mix(in oklab, var(--mint) 40%, var(--border))" }}
                className="p-3 rounded-2xl border border-border bg-surface transition-colors"
              >
                <div className="flex items-start gap-3">
                  <motion.div
                    whileHover={{ rotate: [0, -6, 6, 0] }}
                    className="h-9 w-9 grid place-items-center rounded-xl bg-mint-soft"
                  >
                    <FileText className="h-4 w-4 text-primary" />
                  </motion.div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{f.name}</p>
                    <p className="text-[11px] text-muted-foreground">
                      {f.size_kb} KB · {f.type} · {f.chars.toLocaleString()} ký tự
                    </p>
                  </div>
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", delay: 0.1 }}
                  >
                    <CheckCircle2 className="h-4 w-4 text-mint shrink-0" />
                  </motion.span>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
