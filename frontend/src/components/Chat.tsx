"use client";

import { useEffect, useRef, useState } from "react";
import MessageList from "@/components/MessageList";
import MessageInput from "@/components/MessageInput";
import { streamChat } from "@/lib/api";
import type { Message } from "@/types/chat";

export default function Chat({ initialMessages = [] }: { initialMessages?: Message[] }) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [streaming, setStreaming] = useState(false);
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

    try {
      await streamChat(
        text,
        (chunk) => {
          setMessages((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last.role === "assistant") {
              updated[updated.length - 1] = {
                ...last,
                content: last.content + chunk.content,
              };
            }
            return updated;
          });
        },
        () => setStreaming(false),
        (error) => {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: `エラー: ${error}`,
            };
            return updated;
          });
          setStreaming(false);
        }
      );
    } catch (e) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: `エラー: ${e instanceof Error ? e.message : String(e)}`,
        };
        return updated;
      });
      setStreaming(false);
    }
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
