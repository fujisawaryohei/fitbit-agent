import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import FitbitStatus from "@/components/FitbitStatus";
import Eruda from "@/components/Eruda";

const geist = Geist({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Fitbit AI アシスタント",
  description: "Fitbit データをもとに健康管理をサポートする AI チャット",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja" className={`${geist.className} h-full`} suppressHydrationWarning>
      <body className="h-full flex flex-col bg-gray-50 text-gray-900 antialiased">
        <header className="sticky top-0 z-10 flex items-center justify-between px-5 py-3 bg-[#00B0B9] text-white shrink-0 shadow-sm">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.93V15a1 1 0 0 0-2 0v1.93A8 8 0 0 1 4.07 13H6a1 1 0 0 0 0-2H4.07A8 8 0 0 1 11 4.07V6a1 1 0 0 0 2 0V4.07A8 8 0 0 1 19.93 11H18a1 1 0 0 0 0 2h1.93A8 8 0 0 1 13 16.93z" />
            </svg>
            <span className="text-sm font-semibold tracking-wide">
              Fitbit AI アシスタント
            </span>
          </Link>
          <FitbitStatus />
        </header>
        <main className="flex-1 overflow-hidden">{children}</main>
        {/* デバッグ用 Eruda コンソール（不要になったら削除） */}
        <Eruda />
      </body>
    </html>
  );
}
