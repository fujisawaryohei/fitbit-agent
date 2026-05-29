import type { Chat, ChatMessage, SSEChunk } from "@/types/chat";

export const BACKEND_URL = "/api";

export async function fetchChats(): Promise<Chat[]> {
  const response = await fetch(`${BACKEND_URL}/chats`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`チャット一覧の取得に失敗しました (${response.status})`);
  }
  return response.json();
}

export async function fetchMessages(chatId: number): Promise<ChatMessage[]> {
  const response = await fetch(`${BACKEND_URL}/chats/${chatId}/messages`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`メッセージの取得に失敗しました (${response.status})`);
  }
  return response.json();
}

export async function streamChat(
  message: string,
  onChunk: (chunk: SSEChunk) => void,
  onDone: (chatId?: number) => void,
  onError: (error: string) => void
): Promise<void> {
  let response: Response;

  try {
    response = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      credentials: "include",
    });
  } catch {
    onError("サーバーに接続できません");
    return;
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    onError(body.detail ?? `エラーが発生しました (${response.status})`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError("ストリームを読み取れません");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE は "\n\n" でイベントを区切る
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      for (const line of part.split("\n")) {
        if (!line.startsWith("data: ")) continue;
        try {
          const chunk: SSEChunk = JSON.parse(line.slice(6));
          if (chunk.type === "chunk") onChunk(chunk);
          else if (chunk.type === "done") onDone(chunk.chat_id);
          else if (chunk.type === "error") onError(chunk.content);
        } catch {
          // パース失敗は無視
        }
      }
    }
  }
}
