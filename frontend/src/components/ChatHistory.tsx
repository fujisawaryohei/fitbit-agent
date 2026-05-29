"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchChats } from "@/lib/api";
import type { Chat } from "@/types/chat";
import NewChatModal from "@/components/NewChatModal";

export default function ChatHistory() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  function loadChats() {
    setLoading(true);
    setError(null);
    fetchChats()
      .then((data) => setChats(data))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadChats();
  }, []);

  return (
    <div className="flex h-full w-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 px-3 py-3">
        <span className="text-sm font-semibold text-gray-700">チャット履歴</span>
        <button
          type="button"
          onClick={() => setModalOpen(true)}
          aria-label="新しいチャット"
          className="flex h-7 w-7 items-center justify-center rounded-md text-gray-600 hover:bg-gray-100"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M12 5v14M5 12h14"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-2">
        {loading && <p className="px-2 py-2 text-sm text-gray-400">読み込み中...</p>}
        {error && <p className="px-2 py-2 text-sm text-red-600">{error}</p>}
        {!loading && !error && chats.length === 0 && (
          <p className="px-2 py-2 text-sm text-gray-400">チャットがありません</p>
        )}
        {!loading && !error && chats.length > 0 && (
          <ul className="flex flex-col gap-1">
            {chats.map((chat) => (
              <li key={chat.id}>
                <Link
                  href={`/chat/${chat.id}`}
                  className="block truncate rounded-md px-2 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  title={chat.title}
                >
                  {chat.title}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      <NewChatModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onChatCreated={loadChats}
      />
    </div>
  );
}
