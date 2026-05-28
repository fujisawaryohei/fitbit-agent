"use client";

import { useEffect, useState } from "react";
import { BACKEND_URL } from "@/lib/api";

function getFitbitUserIdFromCookie(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)fitbit_user_id=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export default function FitbitStatus() {
  const [connected, setConnected] = useState<boolean | null>(null);

  useEffect(() => {
    setConnected(getFitbitUserIdFromCookie() !== null);
  }, []);

  if (connected === null) return null;

  return (
    <div className="flex items-center gap-3">
      {connected ? (
        <span className="flex items-center gap-1.5 text-sm text-white/90 font-medium">
          <span className="w-2 h-2 rounded-full bg-white inline-block" />
          接続済み
        </span>
      ) : (
        <a
          href={`${BACKEND_URL}/auth/fitbit`}
          className="text-sm px-3 py-1.5 rounded-md bg-white text-[#00B0B9] font-medium hover:bg-gray-100 transition-colors"
        >
          Fitbit と連携する
        </a>
      )}
    </div>
  );
}