"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { streamChat } from "@/lib/api";

type NewChatModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onChatCreated?: () => void;
};

export default function NewChatModal({ isOpen, onClose, onChatCreated }: NewChatModalProps) {
  const router = useRouter();
  const [text, setText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  async function handleSubmit() {
    const message = text.trim();
    if (!message || streaming) return;

    setStreaming(true);
    setError(null);

    await streamChat(
      message,
      () => {},
      (chatId?: number) => {
        setStreaming(false);
        setText("");
        onClose();
        onChatCreated?.();
        if (chatId != null) {
          router.push(`/chat/${chatId}`);
        } else {
          setError("チャットIDを取得できませんでした");
        }
      },
      (err) => {
        setStreaming(false);
        setError(err);
      }
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg bg-white p-5 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-3 text-base font-semibold text-gray-900">
          新しいチャット
        </h2>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="最初のメッセージを入力..."
          rows={4}
          disabled={streaming}
          className="w-full resize-none rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-[#00B0B9] focus:outline-none disabled:bg-gray-100"
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <div className="mt-4 flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={streaming}
            className="rounded-md px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 disabled:opacity-50"
          >
            キャンセル
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={streaming || text.trim().length === 0}
            className="rounded-md bg-[#00B0B9] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            {streaming ? "送信中..." : "送信"}
          </button>
        </div>
      </div>
    </div>
  );
}
