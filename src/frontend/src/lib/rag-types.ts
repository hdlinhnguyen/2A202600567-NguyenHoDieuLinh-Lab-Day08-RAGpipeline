export type Source = {
  title: string;
  snippet: string;
  page?: number;
  excerpt?: string;
  url?: string;
  links?: string[];
  type?: string;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  /** Trạng thái thinking/reasoning khi chưa có câu trả lời */
  status?: string;
};

export type ChatSession = {
  id: string;
  title: string;
  messages: Message[];
  updatedAt: number;
};
