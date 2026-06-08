import type { Message, Source } from "@/lib/rag-types";

// Dùng relative URL để Vite proxy /api → backend:8000 (tránh lỗi CORS)
const API_BASE = import.meta.env.VITE_RAG_API_URL ?? "";

export type KnowledgeDocument = {
  name: string;
  size_kb: number;
  type: string;
  chars: number;
  status: string;
};

export type KnowledgeBaseInfo = {
  total_documents: number;
  total_chunks: number;
  legal_count: number;
  news_count: number;
  upload_count?: number;
  documents: KnowledgeDocument[];
};

export type UploadResult = {
  success: boolean;
  error?: string;
  filename?: string;
  total_chunks?: number;
  knowledge_base?: KnowledgeBaseInfo;
};

export async function fetchKnowledgeBase(): Promise<KnowledgeBaseInfo> {
  const res = await fetch(`${API_BASE}/api/knowledge-base`);
  if (!res.ok) throw new Error("Không thể tải knowledge base");
  return res.json();
}

export async function uploadDocument(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const text = await res.text();
    return { success: false, error: text || "Upload thất bại" };
  }

  return res.json();
}

export async function sendChatMessage(
  message: string,
  history: Message[],
): Promise<{ answer: string; sources: Source[]; retrieval_source: string }> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      history: history
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({ role: m.role, content: m.content })),
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Chat API lỗi");
  }

  const data = await res.json();
  return {
    answer: data.answer,
    sources: (data.sources ?? []).map((s: Record<string, unknown>) => ({
      title: String(s.title),
      snippet: String(s.snippet),
      excerpt: String(s.excerpt ?? ""),
      url: s.url ? String(s.url) : undefined,
      links: Array.isArray(s.links) ? s.links.map(String) : undefined,
      type: s.type ? String(s.type) : undefined,
    })),
    retrieval_source: data.retrieval_source ?? "hybrid",
  };
}
