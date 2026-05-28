import type { Message } from "@/types/chat";

type Props = {
  messages: Message[];
  streaming: boolean;
};

export default function MessageList({ messages, streaming }: Props) {
  return (
    <div className="flex flex-col gap-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap leading-relaxed ${
              msg.role === "user"
                ? "bg-blue-500 text-white rounded-br-sm"
                : "bg-gray-100 text-gray-800 rounded-bl-sm"
            }`}
          >
            {msg.content}
            {msg.role === "assistant" &&
              streaming &&
              msg === messages[messages.length - 1] && (
                <span className="inline-block w-1.5 h-4 ml-0.5 bg-gray-400 animate-pulse align-middle" />
              )}
          </div>
        </div>
      ))}
    </div>
  );
}
