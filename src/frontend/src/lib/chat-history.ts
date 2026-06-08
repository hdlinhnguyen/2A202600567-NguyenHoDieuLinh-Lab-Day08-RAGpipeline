import type { ChatSession } from "@/lib/rag-types";

const STORAGE_KEY = "arionear-chat-sessions";

export function loadChatSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ChatSession[];
    return parsed.sort((a, b) => b.updatedAt - a.updatedAt);
  } catch {
    return [];
  }
}

export function saveChatSessions(sessions: ChatSession[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

export function upsertChatSession(
  sessions: ChatSession[],
  session: ChatSession,
): ChatSession[] {
  const idx = sessions.findIndex((s) => s.id === session.id);
  const next = idx >= 0
    ? sessions.map((s) => (s.id === session.id ? session : s))
    : [session, ...sessions];
  const sorted = next.sort((a, b) => b.updatedAt - a.updatedAt);
  saveChatSessions(sorted);
  return sorted;
}

export function buildSessionTitle(messages: ChatSession["messages"]): string {
  const firstUser = messages.find((m) => m.role === "user" && m.content.trim());
  if (!firstUser) return "Cuộc trò chuyện mới";
  const text = firstUser.content.trim();
  return text.length > 48 ? `${text.slice(0, 48)}…` : text;
}
