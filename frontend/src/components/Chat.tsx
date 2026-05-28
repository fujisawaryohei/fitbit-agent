"use client";

import { useEffect, useRef, useState } from "react";
import MessageList from "@/components/MessageList";
import MessageInput from "@/components/MessageInput";
import type { Message } from "@/types/chat";

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState(false);
  const sessionId = useRef(crypto.randomUUID());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text: string) {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };
    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "",
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setStreaming(true);

    // TODO: ペアプロで実装
    // streamChat(text, sessionId.current, onChunk, onDone, onError) を呼び出す
    // - onChunk: assistantMessage の content を更新
    // - onDone: setStreaming(false)
    // - onError: エラーメッセージを assistantMessage に設定して setStreaming(false)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <p className="text-center text-gray-400 text-sm mt-16">
            メッセージを送信してチャットを始めましょう
          </p>
        ) : (
          <MessageList messages={messages} streaming={streaming} />
        )}
        <div ref={bottomRef} />
      </div>
      <div className="border-t border-gray-200 px-4 py-3">
        <MessageInput onSend={handleSend} disabled={streaming} />
      </div>
    </div>
  );
}
