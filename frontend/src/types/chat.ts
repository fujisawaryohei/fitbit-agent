export type SSEChunk = {
  type: "chunk" | "done" | "error";
  content: string;
  session_id: string;
  chat_id?: number;
};

export type Chat = {
  id: number;
  title: string;
  created_at: string;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export type ChatMessage = {
  id: number;
  chat_id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
};
