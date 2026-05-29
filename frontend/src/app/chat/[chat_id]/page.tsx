"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Chat from "@/components/Chat";
import { fetchMessages } from "@/lib/api";
import type { Message } from "@/types/chat";

export default function ChatDetailPage() {
  const params = useParams<{ chat_id: string }>();
  const chatId = params.chat_id;

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const chatMessages = await fetchMessages(Number(chatId));
        if (cancelled) return;
        setMessages(
          chatMessages.map((m) => ({
            id: String(m.id),
            role: m.role,
            content: m.content,
          }))
        );
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [chatId]);

  if (loading) {
    return <p className="text-center text-gray-400 text-sm mt-16">読み込み中...</p>;
  }

  if (error) {
    return <p className="text-center text-red-500 text-sm mt-16">エラー: {error}</p>;
  }

  return <Chat initialMessages={messages} />;
}
