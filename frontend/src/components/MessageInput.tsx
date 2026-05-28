"use client";

import { useRef, type KeyboardEvent } from "react";

type Props = {
  onSend: (message: string) => void;
  disabled: boolean;
};

export default function MessageInput({ onSend, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    const value = ref.current?.value.trim();
    if (!value || disabled) return;
    onSend(value);
    if (ref.current) ref.current.value = "";
  }

  return (
    <div className="flex gap-2 items-end">
      <textarea
        ref={ref}
        rows={1}
        disabled={disabled}
        onKeyDown={handleKeyDown}
        placeholder="メッセージを入力（Enter で送信 / Shift+Enter で改行）"
        className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-50 disabled:text-gray-400"
      />
      <button
        onClick={submit}
        disabled={disabled}
        className="px-4 py-2.5 rounded-xl bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        送信
      </button>
    </div>
  );
}
