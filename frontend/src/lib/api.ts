import type { SSEChunk } from "@/types/chat";

export const BACKEND_URL = "/api";

// TODO: ペアプロで実装
// SSE ストリーミングで /chat を呼び出す
// - onChunk: チャンク受信時のコールバック
// - onDone: 完了時のコールバック
// - onError: エラー時のコールバック
export async function streamChat(
  message: string,
  sessionId: string,
  onChunk: (chunk: SSEChunk) => void,
  onDone: () => void,
  onError: (error: string) => void
): Promise<void> {
  throw new Error("Not implemented");
}
