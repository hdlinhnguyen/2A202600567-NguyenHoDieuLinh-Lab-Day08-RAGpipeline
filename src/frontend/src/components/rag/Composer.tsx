import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { PromptInputBox } from "@/components/ui/ai-prompt-box";
import { fadeUp } from "@/lib/motion";
import { useSpeechRecognition } from "@/hooks/useSpeechRecognition";
import { uploadDocument } from "@/lib/api/rag";

const MAX_LEN = 4000;

export function Composer({
  onSend,
  isLoading = false,
}: {
  onSend: (text: string) => void;
  compact?: boolean;
  isLoading?: boolean;
}) {
  const [value, setValue] = useState("");
  const [interim, setInterim] = useState("");

  const appendTranscript = useCallback((text: string) => {
    setValue((prev) => {
      const next = prev ? `${prev} ${text}` : text;
      return next.slice(0, MAX_LEN);
    });
  }, []);

  const { listening, supported, toggle, stop } = useSpeechRecognition({
    lang: "vi-VN",
    onFinalTranscript: appendTranscript,
    onInterimTranscript: setInterim,
  });

  const displayValue = interim
    ? `${value}${value ? " " : ""}${interim}`.slice(0, MAX_LEN)
    : value;

  const handleSend = (message: string) => {
    const text = message.trim();
    if (!text) return;
    onSend(text);
    setValue("");
    setInterim("");
    if (listening) stop();
  };

  const handleValueChange = (next: string) => {
    if (listening) {
      stop();
      setInterim("");
    }
    setValue(next.slice(0, MAX_LEN));
  };

  const handleDocumentSelect = async (file: File) => {
    try {
      const result = await uploadDocument(file);
      if (result.success) {
        toast.success(`Đã thêm "${result.filename}" — ${result.total_chunks} chunks`);
      } else {
        toast.error(result.error ?? "Upload thất bại");
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Upload lỗi");
    }
  };

  return (
    <motion.div
      layout
      variants={fadeUp}
      initial="hidden"
      animate="show"
      className="relative"
    >
      <div className="absolute inset-0 -z-10 mint-glow opacity-40 blur-2xl rounded-3xl pointer-events-none" />
      <PromptInputBox
        value={displayValue}
        onValueChange={handleValueChange}
        onSend={handleSend}
        isLoading={isLoading}
        placeholder="Hỏi về luật pháp, hình phạt, cai nghiện, tin tức nghệ sĩ..."
        onVoiceToggle={supported ? toggle : undefined}
        isVoiceActive={listening}
        voiceSupported={supported}
        onDocumentSelect={handleDocumentSelect}
        documentAccept=".pdf,.docx,.doc,.md,.txt,image/*"
        className="shadow-glow"
      />
    </motion.div>
  );
}
